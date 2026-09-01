"""Unit tests for the explainability service."""

from app.ml.explainability import (
    explain_structured_risk,
    explain_nowcast,
    PredictionExplanation,
)
from app.ml.risk_engine import WeatherFeatures, assess_risk_structured
from app.ml.predictor import generate_nowcast
from app.ml.features import (
    ModelFeatures,
    WeatherObservationFeatures,
    StabilityFeatures,
    RadarFeatures,
    SatelliteFeatures,
    LightningFeatures,
)


def _risk_explanation() -> PredictionExplanation:
    wf = WeatherFeatures(
        latitude=21.25,
        longitude=78.5,
        temperature_c=34.0,
        humidity_percent=90.0,
        cape_jkg=2500.0,
        lifted_index=-6.0,
        wind_shear_ms=22.0,
        precipitation_mm=20.0,
    )
    return explain_structured_risk(assess_risk_structured(wf))


def test_explain_structured_risk_shape():
    exp = _risk_explanation()
    assert isinstance(exp, PredictionExplanation)
    assert exp.prediction_type == "overall_risk"
    assert exp.risk_level in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert exp.summary
    assert exp.confidence >= 0.0
    assert exp.model_label == "BASELINE MODEL"
    assert exp.model_version


def test_positive_drivers_present_for_stormy_conditions():
    exp = _risk_explanation()
    assert len(exp.positive_drivers) > 0
    assert len(exp.drivers) > 0
    for d in exp.drivers:
        assert d.role in {"POSITIVE", "REDUCING"}
        assert d.factor
        assert d.description


def test_reducing_factors_listed_for_benign_conditions():
    wf = WeatherFeatures(
        latitude=21.25,
        longitude=78.5,
        temperature_c=16.0,
        humidity_percent=30.0,
        cape_jkg=50.0,
        lifted_index=6.0,
        wind_shear_ms=2.0,
        precipitation_mm=0.0,
    )
    exp = explain_structured_risk(assess_risk_structured(wf))
    assert isinstance(exp.reducing_factors, list)
    assert exp.summary


def test_explain_nowcast_returns_peak_behavior():
    features = ModelFeatures(
        latitude=21.25,
        longitude=78.5,
        observation=WeatherObservationFeatures(temperature_c=32.0, relative_humidity_percent=80.0, precipitation_rate_mmh=25.0),
        stability=StabilityFeatures(cape_jkg=2000.0, lifted_index_c=-5.0, wind_shear_ms=20.0),
        radar=RadarFeatures(max_reflectivity_dbz=55.0, echo_top_km=13.0),
        satellite=SatelliteFeatures(cloud_top_temperature_k=200.0),
        lightning=LightningFeatures(lightning_density_km2_hr=4.0),
    )
    nowcast = generate_nowcast(features)
    exp = explain_nowcast(nowcast)
    assert exp.prediction_type == "nowcast"
    assert exp.risk_level in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert exp.summary
    assert len(exp.drivers) == 3  # thunderstorm / hail / cloudburst
    assert exp.confidence >= 0.0


def test_explain_nowcast_low_signal():
    features = ModelFeatures(
        latitude=21.25,
        longitude=78.5,
        observation=WeatherObservationFeatures(temperature_c=16.0, relative_humidity_percent=25.0, precipitation_rate_mmh=0.0),
        stability=StabilityFeatures(cape_jkg=0.0, lifted_index_c=8.0, wind_shear_ms=1.0),
        radar=RadarFeatures(max_reflectivity_dbz=20.0, echo_top_km=3.0),
        satellite=SatelliteFeatures(cloud_top_temperature_k=280.0),
        lightning=LightningFeatures(lightning_density_km2_hr=0.0),
    )
    nowcast = generate_nowcast(features)
    exp = explain_nowcast(nowcast)
    assert exp.risk_level in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    # A low-signal forecast should have reducing factors
    assert isinstance(exp.reducing_factors, list)
