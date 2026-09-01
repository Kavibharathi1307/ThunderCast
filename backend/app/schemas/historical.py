"""Pydantic schemas for historical events."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, RiskLevel


class HistoricalEvent(BaseModel):
    """A recorded historical convective weather event."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    event_type: str
    occurred_at: datetime
    latitude: Latitude
    longitude: Longitude
    location_name: str | None = None
    max_thunderstorm_probability: float | None = None
    max_hail_probability: float | None = None
    max_cloudburst_probability: float | None = None
    risk_level: RiskLevel | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    impact_summary: str | None = None
    duration_hours: float | None = Field(default=None, ge=0.0)
    damage_reported: bool = False
