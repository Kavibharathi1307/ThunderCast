"""Pydantic schemas for explainability and model analytics."""

from pydantic import BaseModel, ConfigDict, Field

from .common import RiskLevel


class DriverSchema(BaseModel):
    """A single contributing driver in an explanation."""

    model_config = ConfigDict(extra="forbid")

    factor: str
    role: str  # POSITIVE | REDUCING
    impact: str
    contribution: float = Field(ge=0.0, le=1.0)
    description: str


class ExplanationResponse(BaseModel):
    """A human-readable + structured explanation of a prediction."""

    model_config = ConfigDict(extra="forbid")

    prediction_type: str
    risk_level: RiskLevel
    summary: str
    drivers: list[DriverSchema]
    positive_drivers: list[str]
    reducing_factors: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    model_label: str = "BASELINE MODEL"
    model_version: str = "thundercast-baseline-0.1"


class ModelAnalyticsResponse(BaseModel):
    """Honest model / evaluation analytics report."""

    model_config = ConfigDict(extra="forbid")

    model_label: str
    model_version: str
    architecture: str
    evaluation: dict
    model_status: str = "UNTRAINED"
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO DATA"
    model_name: str = "thundercast-glm"
    dataset: str | None = None
    targets: list[str] = Field(default_factory=list)
    unavailable_targets: list[str] = Field(default_factory=list)
    feature_count: int = 0
    features: list[str] = Field(default_factory=list)
    training_samples: int = 0
    validation_samples: int = 0
    test_samples: int = 0
    metrics: dict = Field(default_factory=dict)
    limitations: str | None = None


class ModelFeatureInfo(BaseModel):
    """Description of a supported feature signal."""

    name: str
    group: str
    description: str
