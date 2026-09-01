"""RiskAssessment schema validation tests."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.risk import RiskAssessment


def _valid_risk(**overrides):
    data = {
        "latitude": 28.6,
        "longitude": 77.2,
        "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "thunderstorm_probability": 0.5,
        "hail_probability": 0.3,
        "cloudburst_probability": 0.2,
        "overall_risk": "HIGH",
        "confidence": 0.7,
        "explanation": "test",
    }
    data.update(overrides)
    return RiskAssessment(**data)


def test_valid_risk_assessment():
    risk = _valid_risk()
    assert risk.overall_risk == "HIGH"
    assert risk.confidence == 0.7


@pytest.mark.parametrize("prob", [-0.1, 1.1, 2.0, -5])
def test_probability_below_or_above_range_rejected(prob):
    with pytest.raises(ValidationError):
        _valid_risk(thunderstorm_probability=prob)


@pytest.mark.parametrize("prob", [0.0, 1.0, 0.5])
def test_probability_boundaries_accepted(prob):
    assert _valid_risk(thunderstorm_probability=prob).thunderstorm_probability == prob


@pytest.mark.parametrize("risk", ["LOW", "MODERATE", "HIGH", "EXTREME"])
def test_valid_risk_levels(risk):
    assert _valid_risk(overall_risk=risk).overall_risk == risk


def test_invalid_risk_level_rejected():
    with pytest.raises(ValidationError):
        _valid_risk(overall_risk="CRITICAL")


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 91.0),
        ("latitude", -91.0),
        ("longitude", 181.0),
        ("longitude", -181.0),
    ],
)
def test_out_of_range_coordinates_rejected(field, value):
    with pytest.raises(ValidationError):
        _valid_risk(**{field: value})
