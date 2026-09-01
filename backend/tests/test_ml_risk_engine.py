"""Unit tests for the risk engine (probability + structured drivers)."""

from app.ml.risk_engine import (
    WeatherFeatures,
    assess_risk,
    assess_risk_structured,
    RiskResult,
    StructuredRisk,
    RiskDriver,
)

LAT, LON = 21.25, 78.5


def _wf(**overrides) -> WeatherFeatures:
    base = WeatherFeatures(
        latitude=LAT,
        longitude=LON,
        temperature_c=32.0,
        humidity_percent=85.0,
        pressure_hpa=1002.0,
        precipitation_mm=20.0,
        cape_jkg=2500.0,
        lifted_index=-6.0,
        wind_shear_ms=25.0,
    )
    base.__dict__.update(overrides)
    return base


def test_assess_risk_returns_bounded_outputs():
    result = assess_risk(_wf())
    assert isinstance(result, RiskResult)
    assert 0.0 <= result.thunderstorm_probability <= 1.0
    assert 0.0 <= result.hail_probability <= 1.0
    assert 0.0 <= result.cloudburst_probability <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.overall_risk in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert result.explanation


def test_assess_risk_tracks_factors():
    result = assess_risk(_wf())
    assert len(result.factors) > 0
    names = {f.name for f in result.factors}
    assert "Humidity" in names
    assert "CAPE" in names
    total_contribution = sum(f.contribution for f in result.factors)
    assert 0.0 <= total_contribution <= 1.5  # contributions can sum past 1 before clamp


def test_high_instability_raises_risk_level():
    high = assess_risk(_wf())
    low = assess_risk(_wf(temperature_c=18.0, humidity_percent=35.0, cape_jkg=100.0, lifted_index=5.0, wind_shear_ms=2.0, precipitation_mm=0.0))
    assert high.thunderstorm_probability > low.thunderstorm_probability


def test_risk_classification_thresholds():
    gentle = assess_risk(_wf(temperature_c=15.0, humidity_percent=30.0, cape_jkg=0.0, lifted_index=8.0, wind_shear_ms=1.0, precipitation_mm=0.0))
    assert gentle.overall_risk in {"LOW", "MODERATE"}


def test_structured_risk_returns_drivers():
    structured = assess_risk_structured(_wf())
    assert isinstance(structured, StructuredRisk)
    assert 0.0 <= structured.risk_score <= 1.0
    assert structured.risk_level in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert len(structured.drivers) > 0
    assert all(isinstance(d, RiskDriver) for d in structured.drivers)
    assert all(d.impact in {"LOW", "MODERATE", "HIGH"} for d in structured.drivers)
    # drivers sorted by contribution descending
    contribs = [d.contribution for d in structured.drivers]
    assert contribs == sorted(contribs, reverse=True)


def test_driver_contributions_bounded():
    structured = assess_risk_structured(_wf())
    for d in structured.drivers:
        assert 0.0 <= d.contribution <= 1.0
        assert d.factor


def test_structured_risk_probabilities_match_plain():
    plain = assess_risk(_wf())
    structured = assess_risk_structured(_wf())
    assert structured.risk_level == plain.overall_risk
    assert round(structured.risk_score, 2) == round(max(plain.thunderstorm_probability, plain.hail_probability, plain.cloudburst_probability), 2)
    assert structured.confidence == plain.confidence


def test_confident_analysis_includes_timestamp():
    result = assess_risk(_wf())
    assert result.timestamp is not None
    structured = assess_risk_structured(_wf())
    assert structured.timestamp is not None
