"""Baseline storm-motion extrapolation.

Given a storm cell's last observed position, speed and direction, predict its
position at fixed look-ahead times (30/60/90/120 min) using constant-velocity
(linear) extrapolation.

LABEL: "Baseline storm-motion extrapolation"
This is NOT a trained deep-learning storm tracker. It assumes steady speed and
direction, which is a transparent, reversible simplification. Real radar
sequence tracking can replace this later without changing call sites.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

# WM: approximate degrees per km at ~20N (WGS84). Slight lat dependence ignored
# for the baseline method.
_KM_PER_DEG_LAT = 111.0
_KM_PER_DEG_LON = 101.7

LOOKAHEAD_MINUTES = (30, 60, 90, 120)

BASELINE_LABEL = "Baseline storm-motion extrapolation"


@dataclass
class PredictedPosition:
    """A predicted storm position at a future time."""

    latitude: float
    longitude: float
    valid_time: datetime
    minutes_ahead: int
    intensity: float  # 0..1


@dataclass
class StormPrediction:
    """Predicted track for one storm cell."""

    cell_id: str
    current_latitude: float
    current_longitude: float
    movement_direction_deg: float
    movement_speed_kmh: float
    current_intensity: float
    predicted_positions: list[PredictedPosition]
    label: str = BASELINE_LABEL


def _radians(deg: float) -> float:
    import math

    return math.radians(deg)


def _displace(
    lat: float,
    lon: float,
    direction_deg: float,
    distance_km: float,
) -> tuple[float, float]:
    """Move (lat, lon) by distance_km along a compass bearing."""
    import math

    bearing = _radians(direction_deg)
    dlat = (distance_km * math.cos(bearing)) / _KM_PER_DEG_LAT
    dlon = (distance_km * math.sin(bearing)) / _KM_PER_DEG_LON
    return round(lat + dlat, 5), round(lon + dlon, 5)


def predict_storm_cell(
    *,
    cell_id: str,
    latitude: float,
    longitude: float,
    movement_direction_deg: float,
    movement_speed_kmh: float,
    current_intensity: float,
    base_time: datetime | None = None,
) -> StormPrediction:
    """Return a StormPrediction using constant-velocity extrapolation."""
    now = base_time or datetime.utcnow()
    predicted: list[PredictedPosition] = []
    for minutes in LOOKAHEAD_MINUTES:
        distance_km = movement_speed_kmh * (minutes / 60.0)
        plat, plon = _displace(
            latitude, longitude, movement_direction_deg, distance_km
        )
        # Intensity slowly relaxes toward a lower regime over the look-ahead.
        intensity = _clamp_intensity(current_intensity * (1.0 - minutes * 0.002))
        predicted.append(
            PredictedPosition(
                latitude=plat,
                longitude=plon,
                valid_time=now + timedelta(minutes=minutes),
                minutes_ahead=minutes,
                intensity=round(intensity, 4),
            )
        )
    return StormPrediction(
        cell_id=cell_id,
        current_latitude=latitude,
        current_longitude=longitude,
        movement_direction_deg=movement_direction_deg,
        movement_speed_kmh=movement_speed_kmh,
        current_intensity=current_intensity,
        predicted_positions=predicted,
    )


def _clamp_intensity(value: float) -> float:
    return max(0.0, min(1.0, value))
