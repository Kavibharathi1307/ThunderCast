"""Weather data service backed by Open-Meteo (real, keyless) with DEMO fallback.

This service is the single seam the rest of the backend uses to obtain current
weather observations. It:

* Requests real Open-Meteo data for latitude/longitude when
  ``ALLOW_EXTERNAL_API`` is enabled (free, no API key required).
* Normalises the response into the existing ``WeatherObservation`` schema.
* Has a short timeout so a slow/unreachable provider never blocks the API.
* Catches every failure and falls back to clearly-labelled DEMO data.
* Returns the semantics of the payload (``REAL`` vs ``DEMO``) explicitly so the
  frontend can show a "LIVE WEATHER DATA" or "DEMO MODE" indicator truthfully.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from ..config import get_settings
from ..data.demo import demo_weather
from ..schemas.weather import WeatherObservation

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 6.0

REAL_PROVENANCE = "REAL WEATHER DATA (Open-Meteo)"
DEMO_PROVENANCE = "DEMO/FALLBACK WEATHER DATA"
DEMO_NOTE = "Fallback demo weather data. Real Open-Meteo data was unavailable."


class OpenMeteoError(RuntimeError):
    """Raised when a real provider cannot supply data (offline/parse error)."""


def get_weather_observation(
    latitude: float, longitude: float
) -> tuple[WeatherObservation, bool, str]:
    """Fetch a real weather observation, falling back to DEMO safely.

    Returns:
        A tuple of ``(observation, is_real, provenance)`` where ``is_real`` is
        ``True`` only when live Open-Meteo data was returned, and ``provenance``
        is a short human-readable source label.
    """
    settings = get_settings()
    if not settings.ALLOW_EXTERNAL_API:
        logger.debug("ALLOW_EXTERNAL_API disabled; returning DEMO weather")
        return _demo_observation(latitude, longitude)

    try:
        observation = _fetch_open_meteo(latitude, longitude)
        return observation, True, REAL_PROVENANCE
    except OpenMeteoError as exc:
        logger.warning(
            "Open-Meteo unavailable for (%s, %s): %s; falling back to DEMO",
            latitude,
            longitude,
            exc,
        )
        return _demo_observation(latitude, longitude)


def _demo_observation(
    latitude: float, longitude: float
) -> tuple[WeatherObservation, bool, str]:
    return demo_weather(latitude, longitude), False, DEMO_PROVENANCE


def _fetch_open_meteo(latitude: float, longitude: float) -> WeatherObservation:
    base = get_settings().OPEN_METEO_FORECAST_URL
    params = {
        "latitude": f"{latitude:.4f}",
        "longitude": f"{longitude:.4f}",
        "current": (
            "temperature_2m,relative_humidity_2m,dew_point_2m,"
            "surface_pressure,wind_speed_10m,wind_direction_10m,"
            "wind_gusts_10m,precipitation,cloud_cover,weather_code"
        ),
        "hourly": "cape,convective_inhibition,lifted_index",
        "timezone": "UTC",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(
            url, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - any transport error = unavailable
        raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc

    current: dict[str, Any] = payload.get("current") or {}
    if "temperature_2m" not in current:
        raise OpenMeteoError("Open-Meteo response missing 'current' block")

    now = datetime.now(timezone.utc)
    return WeatherObservation(
        latitude=latitude,
        longitude=longitude,
        timestamp=now,
        temperature_c=_num(current.get("temperature_2m")),
        humidity_percent=_num(current.get("relative_humidity_2m")),
        wind_speed_ms=_num(current.get("wind_speed_10m")),
        wind_direction_deg=_num(current.get("wind_direction_10m")),
        pressure_hpa=_num(current.get("surface_pressure")),
        precipitation_mm=_num(current.get("precipitation")),
        source="open-meteo",
    )


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_current_weather_payload(
    latitude: float, longitude: float
) -> dict[str, Any]:
    """Return raw current weather variables from Open-Meteo.

    Used by the risk/map services to drive the risk grid from real variables.
    Falls back to demo values on any failure; the ``is_real`` flag tells
    callers which regime the data came from.
    """
    settings = get_settings()
    if not settings.ALLOW_EXTERNAL_API:
        return _demo_raw(latitude, longitude)

    try:
        base = settings.OPEN_METEO_FORECAST_URL
        params = {
            "latitude": f"{latitude:.4f}",
            "longitude": f"{longitude:.4f}",
            "current": (
                "temperature_2m,relative_humidity_2m,dew_point_2m,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,"
                "wind_gusts_10m,precipitation,cloud_cover,weather_code"
            ),
            "hourly": "cape,convective_inhibition,lifted_index",
            "timezone": "UTC",
        }
        url = f"{base}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        current: dict[str, Any] = payload.get("current") or {}
        if not current:
            raise OpenMeteoError("missing current block")
        # Attach the first hourly stability values (current hour) so callers
        # can read CAPE/CIN/lifted-index alongside the surface observation.
        hourly = payload.get("hourly") or {}
        stability = {}
        for api_key, local_key in (
            ("cape", "cape"),
            ("convective_inhibition", "cin"),
            ("lifted_index", "lifted_index"),
        ):
            values = hourly.get(api_key)
            if isinstance(values, list) and values:
                stability[local_key] = values[0]
        current = {**current, **stability}
        return {"current": current, "is_real": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Open-Meteo raw fetch failed for (%s, %s): %s; using DEMO", latitude, longitude, exc
        )
        return _demo_raw(latitude, longitude)


def _demo_raw(latitude: float, longitude: float) -> dict[str, Any]:
    obs = demo_weather(latitude, longitude)
    return {
        "current": {
            "temperature_2m": obs.temperature_c,
            "relative_humidity_2m": obs.humidity_percent,
            "surface_pressure": obs.pressure_hpa,
            "wind_speed_10m": obs.wind_speed_ms,
            "wind_direction_10m": obs.wind_direction_deg,
            "precipitation": obs.precipitation_mm,
            "cloud_cover": None,
            "weather_code": None,
            "cape": None,
            "cin": None,
            "lifted_index": None,
            "dew_point_2m": None,
        },
        "is_real": False,
    }
