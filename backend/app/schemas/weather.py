"""Pydantic schemas for weather observations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude


class WeatherObservation(BaseModel):
    """A single in-situ weather observation for a location."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    timestamp: datetime
    temperature_c: float | None = Field(default=None)
    humidity_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    wind_speed_ms: float | None = Field(default=None, ge=0.0)
    wind_direction_deg: float | None = Field(default=None, ge=0.0, le=360.0)
    pressure_hpa: float | None = Field(default=None, ge=0.0)
    precipitation_mm: float | None = Field(default=None, ge=0.0)
    source: str | None = Field(default=None, description="Data source identifier")
