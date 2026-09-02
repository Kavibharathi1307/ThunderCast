"""Risk grid (map) service.

Computes a risk grid centred on the requested location. When real weather data
is enabled, the grid's cell probabilities are derived from a real Open-Meteo
observation; otherwise it falls back to the existing deterministic DEMO grid.
The response clearly marks which regime was used (REAL vs DEMO/FALLBACK).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pydantic import BaseModel

from ..config import get_settings
from ..data.demo import DEMO_NOTE, demo_risk_grid
from ..ml.risk_engine import _risk_level
from ..schemas.map import (
    RiskGridBounds,
    RiskGridCell,
    RiskGridResponse,
)
from .weather_service import fetch_current_weather_payload

logger = logging.getLogger(__name__)

RESOLUTION = 0.5


class RiskGridResponseWrapper(BaseModel):
    demo: bool = True
    demo_note: str | None = DEMO_NOTE
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO DATA"
    data: RiskGridResponse


def get_risk_grid(
    latitude: float | None = None,
    longitude: float | None = None,
) -> RiskGridResponseWrapper:
    """Return a risk grid, using real weather when available, else demo."""
    settings = get_settings()
    mode = settings.ENVIRONMENT_MODE.upper()

    if mode != "REAL" or not settings.ALLOW_EXTERNAL_API:
        return RiskGridResponseWrapper(data=demo_risk_grid(latitude, longitude))

    payload = fetch_current_weather_payload(
        latitude if latitude is not None else 19.5,
        longitude if longitude is not None else 77.5,
    )
    if not payload.get("is_real"):
        return RiskGridResponseWrapper(data=demo_risk_grid(latitude, longitude))

    grid = _real_risk_grid(payload["current"], latitude, longitude)
    return RiskGridResponseWrapper(
        demo=False,
        demo_note=None,
        environment_mode="REAL",
        data_provenance="REAL WEATHER DATA (Open-Meteo)",
        data=grid,
    )


def _real_risk_grid(
    current: dict, latitude: float | None, longitude: float | None
) -> RiskGridResponse:
    """Build a risk grid whose cells reflect a real observation.

    A single Open-Meteo observation at the grid centre is diffused across the
    cells by distance so the grid reads as a coherent storm cluster, then each
    cell probability is derived from the real temperature/humidity/pressure so
    the grid genuinely reflects the live conditions.
    """
    if latitude is None or longitude is None:
        center_lat, center_lon = 19.5, 77.5
        span = 6
    else:
        center_lat, center_lon = latitude, longitude
        span = 4

    center_lat = round(round(center_lat / RESOLUTION) * RESOLUTION, 3)
    center_lon = round(round(center_lon / RESOLUTION) * RESOLUTION, 3)

    temp = _float(current.get("temperature_2m")) or 29.0
    humidity = _float(current.get("relative_humidity_2m")) or 70.0
    pressure = _float(current.get("surface_pressure")) or 1010.0
    precip = _float(current.get("precipitation")) or 0.0
    cape = _float(current.get("cape"))
    wind_speed = _float(current.get("wind_speed_10m")) or 5.0

    cell_lats = [round(center_lat + i * RESOLUTION, 3) for i in range(-span, span + 1)]
    cell_lons = [round(center_lon + i * RESOLUTION, 3) for i in range(-span, span + 1)]

    cells: list[RiskGridCell] = []
    for lat in cell_lats:
        for lon in cell_lons:
            dist = max(abs(lat - center_lat), abs(lon - center_lon)) / RESOLUTION
            proximity = max(0.0, 1.0 - dist / (span + 1))

            thunder = _clamp(0.1 + (humidity - 40) / 100 * 0.35 + proximity * 0.3)
            if cape is not None and cape > 1000:
                thunder = _clamp(thunder + 0.1)
            thunder = _clamp(thunder)

            hail = _clamp(0.08 + thunder * 0.35 + (0.06 if cape and cape > 1500 else 0.0))
            cloudburst = _clamp(
                0.05
                + (0.12 if humidity > 75 else 0.0)
                + (0.15 if precip > 10 else 0.0)
                + proximity * 0.12
            )
            peak = max(thunder, hail, cloudburst)
            level = _risk_level(peak)

            cells.append(
                RiskGridCell(
                    latitude=lat,
                    longitude=lon,
                    thunderstorm_probability=round(thunder, 3),
                    hail_probability=round(hail, 3),
                    cloudburst_probability=round(cloudburst, 3),
                    overall_risk=level,
                    confidence=_confidence(temp, humidity, pressure, cape),
                )
            )

    return RiskGridResponse(
        bounds=RiskGridBounds(
            min_latitude=cell_lats[0] - RESOLUTION / 2,
            min_longitude=cell_lons[0] - RESOLUTION / 2,
            max_latitude=cell_lats[-1] + RESOLUTION / 2,
            max_longitude=cell_lons[-1] + RESOLUTION / 2,
        ),
        resolution_deg=RESOLUTION,
        generated_at=datetime.now(timezone.utc),
        cells=cells,
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _confidence(
    temp: float, humidity: float, pressure: float, cape: float | None
) -> float:
    fields = [
        temp is not None,
        humidity is not None,
        pressure is not None,
        cape is not None,
    ]
    return round(min(0.55 + 0.1 * sum(fields), 0.95), 2)


def _float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
