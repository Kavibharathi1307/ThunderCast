"""ForecastPoint schema validation tests."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.forecast import ForecastPoint


def _valid_point(**overrides):
    data = {
        "latitude": 28.6,
        "longitude": 77.2,
        "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "lead_time_hours": 2.0,
        "thunderstorm_probability": 0.5,
        "hail_probability": 0.3,
        "cloudburst_probability": 0.2,
    }
    data.update(overrides)
    return ForecastPoint(**data)


def test_valid_forecast_point():
    p = _valid_point()
    assert p.lead_time_hours == 2.0


def test_lead_time_within_window_accepted():
    assert _valid_point(lead_time_hours=6.0).lead_time_hours == 6.0
    assert _valid_point(lead_time_hours=0.0).lead_time_hours == 0.0


@pytest.mark.parametrize("lead", [-1.0, 6.5, 7.0])
def test_lead_time_outside_0_6_hours_rejected(lead):
    with pytest.raises(ValidationError):
        _valid_point(lead_time_hours=lead)


@pytest.mark.parametrize("prob", [-0.1, 1.1])
def test_probability_out_of_range_rejected(prob):
    with pytest.raises(ValidationError):
        _valid_point(thunderstorm_probability=prob)
