"""Pydantic schemas for nowcasting and impact-based risk."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, Probability, RiskLevel


class NowcastPointSchema(BaseModel):
    """A single nowcast point for a location and horizon."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    forecast_time: datetime
    horizon_hours: int = Field(ge=1, le=6)
    thunderstorm_probability: Probability
    hail_probability: Probability
    cloudburst_probability: Probability
    overall_risk: RiskLevel
    confidence: Probability
    model_label: str = "BASELINE MODEL"
    model_version: str = "thundercast-baseline-0.1"


class NowcastResponse(BaseModel):
    """Full 0-6 hour nowcast for a location."""

    model_config = ConfigDict(extra="forbid")

    demo: bool = True
    demo_note: str
    latitude: Latitude
    longitude: Longitude
    forecast_time: datetime
    window_hours: int = 6
    peak_risk: RiskLevel
    peak_hour: int | None = None
    risk_start_hour: int | None = None
    risk_end_hour: int | None = None
    model_label: str = "BASELINE MODEL"
    model_version: str = "thundercast-baseline-0.1"
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO DATA"
    points: list[NowcastPointSchema]


class ImpactResponse(BaseModel):
    """Impact-based risk scores (0..1) for multiple categories."""

    model_config = ConfigDict(extra="forbid")

    demo: bool = True
    demo_note: str
    latitude: Latitude
    longitude: Longitude
    label: str = "PROTOTYPE IMPACT MODEL"
    impacts: dict[str, float]


class NowcastImpactResponse(BaseModel):
    """Combined nowcast + impact assessment for the dashboard."""

    model_config = ConfigDict(extra="forbid")

    demo: bool = True
    demo_note: str
    nowcast: NowcastResponse
    impacts: ImpactResponse
