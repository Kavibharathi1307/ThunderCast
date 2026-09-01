"""Pydantic schemas for alerts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, RiskLevel


class AlertImpact(BaseModel):
    """Detailed impact information for an alert."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(description="Impact category: e.g. flooding, wind_damage, power_outage")
    severity_description: str = Field(description="Human-readable impact description")
    affected_population: str | None = Field(default=None, description="Estimated affected population range")
    recommended_action: str = Field(description="Recommended action for the affected area")


class Alert(BaseModel):
    """An impact-based alert for a geographic area."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    title: str
    message: str
    severity: RiskLevel
    area_name: str | None = Field(default=None, description="Human-readable area name")
    area_latitude: Latitude
    area_longitude: Longitude
    area_radius_km: float | None = Field(default=None, ge=0.0, description="Alert coverage radius")
    issued_at: datetime
    valid_until: datetime
    impacts: list[AlertImpact] = Field(default_factory=list)
    source: str = "ThunderCast AI"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
