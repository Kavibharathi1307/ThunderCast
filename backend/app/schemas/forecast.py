"""Pydantic schemas for forecasts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, Probability


class ForecastPoint(BaseModel):
    """A single forecast point for a given location and lead time."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    timestamp: datetime
    lead_time_hours: float = Field(ge=0.0, le=6.0)
    thunderstorm_probability: Probability
    hail_probability: Probability
    cloudburst_probability: Probability
    precipitation_mm: float | None = None
    wind_speed_ms: float | None = None
