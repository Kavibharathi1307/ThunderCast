"""Real-data providers backed by free public meteorological APIs.

DataSource choice
-----------------
Open-Meteo (https://open-meteo.com) is free, requires **no API key**, and its
forecast API exposes exactly the convective features this MVP needs:

* temperature, dew point, relative humidity, surface pressure, wind speed
* precipitation / precipitation rate
* cloud cover
* CAPE, convective inhibition (CIN), lifted index, wind gusts (shear proxy)

It therefore plugs straight into the existing provider ABCs
(:class:`WeatherDataProvider` etc.) which the prediction engine already consumes.

Design / honesty
----------------
* Everyone is clearly labelled ``REAL DATA`` via ``provenance``.
* Providers use only the Python standard library (``urllib.request``), so no
  new dependencies are introduced.
* Outbound calls are gated behind ``settings.ALLOW_EXTERNAL_API``. When that is
  off, the provider is unreachable by construction (tests / offline).
* On any network/parse error the provider raises ``ProviderUnavailable`` so the
  service can gracefully fall back to DEMO rather than serving broken data.

A radar/satellite/lightning provider would need a keyed or region-specific feed
(e.g. IMD for India); those remain DEMO-flagged until a public source is
plugged in, which is reported honestly.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request

from .features import (
    ModelFeatures,
    WeatherObservationFeatures,
    StabilityFeatures,
    RadarFeatures,
    SatelliteFeatures,
    LightningFeatures,
)
from .providers import (
    WeatherDataProvider,
    RadarDataProvider,
    SatelliteDataProvider,
    LightningDataProvider,
    DemoDataProvider,
)
from ..config import get_settings

logger = logging.getLogger(__name__)

REAL_PROVENANCE_LABEL = "REAL DATA (Open-Meteo)"
REQUEST_TIMEOUT_SECONDS = 8.0


class ProviderUnavailable(RuntimeError):
    """Raised when a real provider cannot supply data (offline/parse error)."""


class OpenMeteoWeatherProvider(WeatherDataProvider):
    """Real surface + thermodynamic observations from Open-Meteo."""

    provenance: str = REAL_PROVENANCE_LABEL

    def __init__(self, base_url: str | None = None, allowed: bool | None = None) -> None:
        self.base_url = base_url or get_settings().OPEN_METEO_FORECAST_URL
        self.allowed = (
            get_settings().ALLOW_EXTERNAL_API if allowed is None else allowed
        )

    def get_observation(self, latitude: float, longitude: float) -> WeatherObservationFeatures:
        data = self._fetch(latitude, longitude)
        current = data.get("current", {})
        return WeatherObservationFeatures(
            temperature_c=_num(current.get("temperature_2m")),
            dew_point_c=_num(current.get("dew_point_2m")),
            relative_humidity_percent=_num(current.get("relative_humidity_2m")),
            pressure_hpa=_num(current.get("surface_pressure")),
            wind_speed_ms=_num(current.get("wind_speed_10m")),
            wind_direction_deg=_num(current.get("wind_direction_10m")),
            precipitation_mm=_num(current.get("precipitation")),
            precipitation_rate_mmh=_num(current.get("precipitation_rate")),
            cloud_cover_percent=_num(current.get("cloud_cover")),
        )

    def get_stability(self, latitude: float, longitude: float) -> StabilityFeatures:
        current = self._fetch(latitude, longitude).get("current", {})
        return StabilityFeatures(
            cape_jkg=_num(current.get("cape")),
            cin_jkg=_num(current.get("cin")),
            lifted_index_c=_num(current.get("lifted_index")),
            wind_shear_ms=_num(current.get("wind_gusts_10m")),
            dewpoint_depression_c=_dewpoint_depression(current.get("temperature_2m"), current.get("dew_point_2m")),
        )

    def build_features(self, latitude: float, longitude: float) -> ModelFeatures:
        obs = self.get_observation(latitude, longitude)
        return ModelFeatures(
            latitude=latitude,
            longitude=longitude,
            observation=obs,
            stability=self.get_stability(latitude, longitude),
            radar=RadarFeatures(),
            satellite=SatelliteFeatures(),
            lightning=LightningFeatures(),
        )

    def _fetch(self, latitude: float, longitude: float) -> dict:
        if not self.allowed:
            raise ProviderUnavailable(
                "outbound API calls disabled (ALLOW_EXTERNAL_API=false)"
            )
        params = {
            "latitude": f"{latitude:.4f}",
            "longitude": f"{longitude:.4f}",
            "current": (
                "temperature_2m,relative_humidity_2m,dew_point_2m,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,"
                "wind_gusts_10m,precipitation,cloud_cover"
            ),
            "hourly": "cape,convective_inhibition,lifted_index",
            "timezone": "UTC",
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - any transport error means unavailable
            raise ProviderUnavailable(f"Open-Meteo request failed: {exc}") from exc
        if "current" not in payload:
            raise ProviderUnavailable("Open-Meteo response missing 'current' block")
        current = payload.get("current", {})
        # Merge the first hourly stability values (current hour) into the
        # current block so CAPE / CIN / lifted-index are available.
        hourly = payload.get("hourly") or {}
        for api_key, local_key in (
            ("cape", "cape"),
            ("convective_inhibition", "cin"),
            ("lifted_index", "lifted_index"),
        ):
            values = hourly.get(api_key)
            if isinstance(values, list) and values:
                current[local_key] = values[0]
        return payload


class RealWeatherProvider(
    WeatherDataProvider,
    RadarDataProvider,
    SatelliteDataProvider,
    LightningDataProvider,
):
    """Composite real-data provider.

    Surface/thermodynamic signals come from Open-Meteo. Radar, satellite and
    lightning have no bundled public source yet, so for those it explicitly
    returns empty features (unknown) rather than demo values, keeping the output
    honestly REAL-flagged without inventing signals.

    If Open-Meteo is unavailable it raises ``ProviderUnavailable`` so the
    service can fall back to DEMO.
    """

    provenance: str = REAL_PROVENANCE_LABEL

    def __init__(self, weather: OpenMeteoWeatherProvider | None = None) -> None:
        self.weather = weather or OpenMeteoWeatherProvider()

    def get_observation(self, latitude: float, longitude: float) -> WeatherObservationFeatures:
        return self.weather.get_observation(latitude, longitude)

    def get_radar(self, latitude: float, longitude: float) -> RadarFeatures:
        return RadarFeatures()

    def get_satellite(self, latitude: float, longitude: float) -> SatelliteFeatures:
        return SatelliteFeatures()

    def get_lightning(self, latitude: float, longitude: float) -> LightningFeatures:
        return LightningFeatures()

    def build_features(self, latitude: float, longitude: float) -> ModelFeatures:
        return self.weather.build_features(latitude, longitude)


def resolve_feature_provider(allowed: bool | None = None) -> WeatherDataProvider:
    """Return the REAL composite provider when enabled, else the demo provider.

    The decision is driven by ``ENVIRONMENT_MODE``; it never silently mixes
    modes. When in REAL mode but the network is unavailable, the caller must
    catch ``ProviderUnavailable`` and fall back to DEMO with a clear label.
    """
    settings = get_settings()
    mode = settings.ENVIRONMENT_MODE.upper()
    if mode == "REAL":
        return RealWeatherProvider(
            OpenMeteoWeatherProvider(allowed=settings.ALLOW_EXTERNAL_API if allowed is None else allowed)
        )
    return DemoDataProvider()


def _num(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _dewpoint_depression(temp, dew):
    if temp is None or dew is None:
        return None
    return float(temp) - float(dew)
