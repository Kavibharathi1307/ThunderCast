"""Pydantic schemas for the geospatial risk grid."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, Probability, RiskLevel

MAX_GRID_COLUMNS = 300
MAX_GRID_ROWS = 300


class RiskGridBounds(BaseModel):
    """Bounds describing a rectangular geographic region."""

    model_config = ConfigDict(extra="forbid")

    min_latitude: Latitude
    min_longitude: Longitude
    max_latitude: Latitude
    max_longitude: Longitude


class RiskGridCell(BaseModel):
    """A single cell within the risk grid."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    thunderstorm_probability: Probability
    hail_probability: Probability
    cloudburst_probability: Probability
    overall_risk: RiskLevel
    confidence: Probability


class RiskGridResponse(BaseModel):
    """Full risk grid response."""

    model_config = ConfigDict(extra="forbid")

    bounds: RiskGridBounds
    resolution_deg: float = Field(gt=0.0)
    generated_at: datetime
    cells: list[RiskGridCell]
