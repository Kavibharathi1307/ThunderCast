"""Data-provider interfaces and a DemoDataProvider.

Design (Phase 10)
-----------------
The prediction engine consumes a single ``ModelFeatures`` bundle and never
cares where the data came from. Providers are the seam where real data can be
plugged in later:

* WeatherDataProvider
* RadarDataProvider
* SatelliteDataProvider
* LightningDataProvider

Today the system ships a ``DemoDataProvider`` that builds deterministic demo
``ModelFeatures`` from the existing demo generators. Every provider is clearly
labelled as supplying DEMO data, so the engine can tag its outputs honestly.
"""

from __future__ import annotations

import abc
import random as _random
import hashlib

from .features import (
    ModelFeatures,
    WeatherObservationFeatures,
    StabilityFeatures,
    RadarFeatures,
    SatelliteFeatures,
    LightningFeatures,
)

DATA_PROVENANCE_LABEL = "DEMO DATA"


def _seed_from_coords(lat: float, lon: float, sal: int = 0) -> int:
    key = f"thundercast:{lat:.4f}:{lon:.4f}:{sal}"
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


class WeatherDataProvider(abc.ABC):
    """Interface for surface weather observations."""

    def get_observation(self, latitude: float, longitude: float) -> WeatherObservationFeatures:
        raise NotImplementedError


class RadarDataProvider(abc.ABC):
    """Interface for radar-derived features."""

    def get_radar(self, latitude: float, longitude: float) -> RadarFeatures:
        raise NotImplementedError


class SatelliteDataProvider(abc.ABC):
    """Interface for satellite-derived features."""

    def get_satellite(self, latitude: float, longitude: float) -> SatelliteFeatures:
        raise NotImplementedError


class LightningDataProvider(abc.ABC):
    """Interface for lightning-density features."""

    def get_lightning(self, latitude: float, longitude: float) -> LightningFeatures:
        raise NotImplementedError


class DemoDataProvider(WeatherDataProvider, RadarDataProvider, SatelliteDataProvider, LightningDataProvider):
    """Deterministic demo provider building ModelFeatures per coordinate.

    Clearly labelled DEMO DATA: values are derived from a per-coordinate seed,
    which keeps responses consistent across calls without pretending to be
    real observations.
    """

    #: What to read from the obs to expose as stability/radar proxies.
    provenance: str = DATA_PROVENANCE_LABEL

    def _moisture_level(self, lat: float, lon: float) -> float:
        return 50.0 + (_random.Random(_seed_from_coords(lat, lon, 10)).random() * 48.0)

    def get_observation(self, latitude: float, longitude: float) -> WeatherObservationFeatures:
        rng = _random.Random(_seed_from_coords(latitude, longitude, 1))
        humidity = self._moisture_level(latitude, longitude)
        temp = 24.0 + rng.random() * 12.0
        dew = max(temp - (10.0 - rng.random() * 14.0), -5.0)
        precip_rate = rng.random() * 35.0 if humidity > 68 else rng.random() * 4.0
        return WeatherObservationFeatures(
            temperature_c=round(temp, 1),
            dew_point_c=round(dew, 1),
            relative_humidity_percent=round(humidity, 1),
            pressure_hpa=round(1002.0 + rng.random() * 14.0, 1),
            wind_speed_ms=round(2.0 + rng.random() * 10.0, 1),
            wind_direction_deg=round(rng.random() * 360.0, 1),
            precipitation_mm=round(rng.random() * 6.0, 1),
            precipitation_rate_mmh=round(precip_rate, 1),
            cloud_cover_percent=round(45.0 + rng.random() * 55.0, 1),
        )

    def get_radar(self, latitude: float, longitude: float) -> RadarFeatures:
        rng = _random.Random(_seed_from_coords(latitude, longitude, 2))
        intensity = 0.2 + rng.random() * 0.6
        return RadarFeatures(
            max_reflectivity_dbz=round(30.0 + rng.random() * 30.0, 1),
            echo_top_km=round(6.0 + rng.random() * 8.0, 1),
            vil_kgm2=round(10.0 + rng.random() * 40.0, 1),
            cell_movement_speed_kmh=round(10.0 + rng.random() * 30.0, 1),
            cell_movement_direction_deg=round(rng.random() * 360.0, 1),
            cell_intensity=round(intensity, 3),
        )

    def get_satellite(self, latitude: float, longitude: float) -> SatelliteFeatures:
        rng = _random.Random(_seed_from_coords(latitude, longitude, 3))
        return SatelliteFeatures(
            cloud_top_temperature_k=round(200.0 + rng.random() * 50.0, 1),
            cloud_top_pressure_hpa=round(300.0 + rng.random() * 150.0, 1),
        )

    def get_lightning(self, latitude: float, longitude: float) -> LightningFeatures:
        rng = _random.Random(_seed_from_coords(latitude, longitude, 4))
        return LightningFeatures(lightning_density_km2_hr=round(rng.random() * 6.0, 3))

    def build_features(self, latitude: float, longitude: float) -> ModelFeatures:
        """Assemble a full ModelFeatures bundle from the demo provider."""
        obs = self.get_observation(latitude, longitude)
        return ModelFeatures(
            latitude=latitude,
            longitude=longitude,
            observation=obs,
            stability=StabilityFeatures(
                cape_jkg=round((obs.temperature_c + obs.relative_humidity_percent - 60) * 40.0, 1),
                lifted_index_c=round(3.0 - (obs.relative_humidity_percent * 0.08), 1),
                wind_shear_ms=self.get_radar(latitude, longitude).cell_movement_speed_kmh * 0.4,
            ),
            radar=self.get_radar(latitude, longitude),
            satellite=self.get_satellite(latitude, longitude),
            lightning=self.get_lightning(latitude, longitude),
        )
