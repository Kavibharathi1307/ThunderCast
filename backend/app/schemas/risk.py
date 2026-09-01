"""Pydantic schemas for risk assessments."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Latitude, Longitude, Probability, RiskLevel
from .weather import WeatherObservation
from .forecast import ForecastPoint


class RiskFactor(BaseModel):
    """A single contributing factor to a risk assessment."""

    model_config = ConfigDict(extra="forbid")

    name: str
    contribution: Probability
    description: str


class RiskAssessment(BaseModel):
    """A convective risk assessment for a specific location and time."""

    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude
    timestamp: datetime
    thunderstorm_probability: Probability
    hail_probability: Probability
    cloudburst_probability: Probability
    overall_risk: RiskLevel
    confidence: Probability
    explanation: str | None = None
    risk_factors: list[RiskFactor] = Field(default_factory=list)


class RiskResponse(RiskAssessment):
    """Full risk response, optionally including supporting inputs."""

    weather: WeatherObservation | None = None
    forecast: ForecastPoint | None = None
