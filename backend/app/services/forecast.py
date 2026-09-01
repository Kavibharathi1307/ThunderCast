"""Forecast service: 0-6 hour nowcast points (demo at this stage)."""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_forecast
from ..schemas.forecast import ForecastPoint
from .intelligence import environment_mode, current_provenance


class ForecastResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    latitude: float
    longitude: float
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO DATA"
    points: list[ForecastPoint]


def get_forecast(latitude: float, longitude: float) -> ForecastResponse:
    return ForecastResponse(
        latitude=latitude,
        longitude=longitude,
        environment_mode=environment_mode(),
        data_provenance=current_provenance(),
        points=demo_forecast(latitude, longitude),
    )
