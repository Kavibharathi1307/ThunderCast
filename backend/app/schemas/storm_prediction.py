"""Pydantic schemas for storm-motion predictions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, Probability


class PredictedPositionSchema(BaseModel):
    """A predicted storm position at a future time."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    valid_time: datetime
    minutes_ahead: int = Field(ge=0)
    intensity: Probability


class StormPredictionSchema(BaseModel):
    """Predicted track for one storm cell."""

    model_config = ConfigDict(extra="forbid")

    cell_id: str
    current_latitude: Latitude
    current_longitude: Longitude
    movement_direction_deg: float = Field(ge=0.0, le=360.0)
    movement_speed_kmh: float = Field(ge=0.0)
    current_intensity: Probability
    label: str = "Baseline storm-motion extrapolation"
    predicted_positions: list[PredictedPositionSchema]


class StormPredictionResponse(BaseModel):
    """List of storm-motion predictions."""

    model_config = ConfigDict(extra="forbid")

    demo: bool = True
    demo_note: str
    count: int
    predictions: list[StormPredictionSchema]
    label: str = "Baseline storm-motion extrapolation"
