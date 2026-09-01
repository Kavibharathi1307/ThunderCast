"""Pydantic schemas for storm cell tracking."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, Probability, RiskLevel


class StormCell(BaseModel):
    """A detected convective storm cell with tracking data."""

    model_config = ConfigDict(extra="forbid")

    id: str
    latitude: Latitude
    longitude: Longitude
    intensity: Probability = Field(description="Normalized intensity 0-1")
    severity: RiskLevel
    radius_km: float = Field(ge=0.0, description="Approximate cell radius in km")
    movement_speed_kmh: float = Field(ge=0.0)
    movement_direction_deg: float = Field(ge=0.0, le=360.0)
    timestamp: datetime
    precipitation_mm_h: float = Field(ge=0.0, description="Precipitation rate mm/h")
    echo_top_km: float | None = Field(default=None, ge=0.0)
    vil_kgm2: float | None = Field(default=None, ge=0.0, description="Vertically integrated liquid")


class StormTrack(BaseModel):
    """Historical and projected positions of a storm cell."""

    model_config = ConfigDict(extra="forbid")

    cell_id: str
    positions: list["StormCellPosition"]
    projected_positions: list["StormCellPosition"]


class StormCellPosition(BaseModel):
    """A single position in a storm cell's track."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    timestamp: datetime
    intensity: Probability


StormTrack.model_rebuild()
