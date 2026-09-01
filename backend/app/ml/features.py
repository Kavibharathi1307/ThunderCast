"""Meteorological feature schema and feature-extraction layer.

Goal
----
Provide a clean, typed feature schema so that real weather / radar /
satellite / lightning / NWP data can later be plugged in without rewriting
the prediction engine.

All features are read-only dataclasses with optional fields, so a provider
may supply as many signals as it has. The prediction engine treats missing
features conservatively (no fabricated observations).

Provenance / honesty
--------------------
This module never *invents* real observations. When a full observation set is
not available, providers supply clearly-labelled demo/baseline data, and the
engine marks its outputs accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WeatherObservationFeatures:
    """In-situ surface weather observation features (all optional units fixed)."""

    temperature_c: float | None = None
    dew_point_c: float | None = None
    relative_humidity_percent: float | None = None
    pressure_hpa: float | None = None
    wind_speed_ms: float | None = None
    wind_direction_deg: float | None = None
    precipitation_mm: float | None = None
    precipitation_rate_mmh: float | None = None
    cloud_cover_percent: float | None = None


@dataclass
class StabilityFeatures:
    """Atmospheric stability / thermodynamic indices."""

    cape_jkg: float | None = None
    cin_jkg: float | None = None
    lifted_index_c: float | None = None
    wind_shear_ms: float | None = None
    dewpoint_depression_c: float | None = None


@dataclass
class RadarFeatures:
    """Radar-derived features."""

    max_reflectivity_dbz: float | None = None
    echo_top_km: float | None = None
    vil_kgm2: float | None = None
    cell_movement_speed_kmh: float | None = None
    cell_movement_direction_deg: float | None = None
    cell_intensity: float | None = None  # 0..1 normalized


@dataclass
class SatelliteFeatures:
    """Satellite-imagery-derived features."""

    cloud_top_temperature_k: float | None = None
    cloud_top_pressure_hpa: float | None = None


@dataclass
class LightningFeatures:
    """Lightning-density features."""

    lightning_density_km2_hr: float | None = None


@dataclass
class ModelFeatures:
    """Aggregated feature bundle passed to the prediction engine.

    Only fields actually known to the caller should be set. The engine reads
    wholesale from this object; any unset field is treated as "unknown".
    """

    latitude: float
    longitude: float
    observation: WeatherObservationFeatures = field(default_factory=WeatherObservationFeatures)
    stability: StabilityFeatures = field(default_factory=StabilityFeatures)
    radar: RadarFeatures = field(default_factory=RadarFeatures)
    satellite: SatelliteFeatures = field(default_factory=SatelliteFeatures)
    lightning: LightningFeatures = field(default_factory=LightningFeatures)


def derived_relative_humidity(
    temperature_c: float, dew_point_c: float
) -> float | None:
    """Magnus-formula relative humidity (0..100) from temperature + dew point.

    Returns ``None`` if inputs are missing, so callers can treat the value as
    unknown rather than fabricating it.
    """
    if temperature_c is None or dew_point_c is None:
        return None
    es = _saturation_vapor_pressure(temperature_c)
    e = _saturation_vapor_pressure(dew_point_c)
    if es <= 0:
        return None
    return max(0.0, min(100.0, (e / es) * 100.0))


def _saturation_vapor_pressure(temp_c: float) -> float:
    """Bolton/Magnus approximation of saturation vapour pressure (hPa)."""
    return 6.112 * (2.718281828459045 ** ((17.67 * temp_c) / (temp_c + 243.5)))
