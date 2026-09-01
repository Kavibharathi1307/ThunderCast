"""Unit tests for the 0-6 hour nowcasting engine (predictor)."""

from datetime import datetime, timezone

import pytest

from app.ml.features import (
    ModelFeatures,
    WeatherObservationFeatures,
    StabilityFeatures,
    RadarFeatures,
    SatelliteFeatures,
    LightningFeatures,
)
from app.ml.predictor import (
    generate_nowcast,
    HORIZONS_HOURS,
    NowcastResult,
    NowcastPoint,
)
from app.ml.thresholds import BASELINE_THRESHOLDS

LAT, LON = 21.25, 78.5


def _features(**overrides) -> ModelFeatures:
    base = ModelFeatures(
        latitude=LAT,
        longitude=LON,
        observation=WeatherObservationFeatures(
            temperature_c=30.0,
            relative_humidity_percent=75.0,
            precipitation_rate_mmh=20.0,
            precipitation_mm=15.0,
        ),
        stability=StabilityFeatures(
            cape_jkg=1800.0,
            lifted_index_c=-4.0,
            wind_shear_ms=18.0,
        ),
        radar=RadarFeatures(
            max_reflectivity_dbz=50.0,
            echo_top_km=12.0,
        ),
        satellite=SatelliteFeatures(cloud_top_temperature_k=205.0),
        lightning=LightningFeatures(lightning_density_km2_hr=3.0),
    )
    if overrides:
        obs = base.observation
        stab = base.stability
        rad = base.radar
        sat = base.satellite
        ltg = base.lightning
        for key, value in overrides.items():
            for obj, name in (
                (obs, "observation"),
                (stab, "stability"),
                (rad, "radar"),
                (sat, "satellite"),
                (ltg, "lightning"),
            ):
                if key.startswith(name + "__"):
                    setattr(obj, key.split("__", 1)[1], value)
                    break
            else:
                setattr(base, key, value)
    return base


def test_generate_nowcast_returns_full_result():
    features = _features()
    result = generate_nowcast(features)
    assert isinstance(result, NowcastResult)
    assert result.latitude == LAT
    assert result.longitude == LON
    assert result.window_hours == 6
    assert len(result.points) == 6
    assert result.peak_risk in {"LOW", "MODERATE", "HIGH", "EXTREME"}


def test_horizons_are_1_to_6():
    assert HORIZONS_HOURS == [1, 2, 3, 4, 5, 6]


def test_each_point_has_expected_fields_and_bounds():
    result = generate_nowcast(_features())
    for p in result.points:
        assert isinstance(p, NowcastPoint)
        assert 1 <= p.horizon_hours <= 6
        assert 0.0 <= p.thunderstorm_probability <= 1.0
        assert 0.0 <= p.hail_probability <= 1.0
        assert 0.0 <= p.cloudburst_probability <= 1.0
        assert 0.0 <= p.confidence <= 1.0
        assert p.overall_risk in {"LOW", "MODERATE", "HIGH", "EXTREME"}
        assert p.forecast_time > result.forecast_time
        assert p.forecast_time.tzinfo is not None
        assert p.model_label == "BASELINE MODEL"
        assert p.model_version


def test_forecast_times_advance_by_one_hour_each():
    result = generate_nowcast(_features(), forecast_time=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))
    hours = [p.forecast_time.hour for p in result.points]
    assert hours == [1, 2, 3, 4, 5, 6]
    assert all(p.horizon_hours == i for i, p in zip(HORIZONS_HOURS, result.points))


def test_probabilities_remain_bounded_for_extreme_inputs():
    extreme = _features(
        observation__temperature_c=50.0,
        observation__relative_humidity_percent=100.0,
        observation__precipitation_rate_mmh=200.0,
        stability__cape_jkg=10000.0,
        stability__lifted_index_c=-20.0,
        stability__wind_shear_ms=100.0,
        radar__max_reflectivity_dbz=80.0,
        radar__echo_top_km=20.0,
        lightning__lightning_density_km2_hr=50.0,
    )
    result = generate_nowcast(extreme)
    for p in result.points:
        assert 0.0 <= p.thunderstorm_probability <= 1.0
        assert 0.0 <= p.hail_probability <= 1.0
        assert 0.0 <= p.cloudburst_probability <= 1.0


def test_high_convective_inputs_yield_higher_risk_than_benign():
    stormy = generate_nowcast(_features())
    calm = generate_nowcast(
        _features(
            observation__temperature_c=15.0,
            observation__relative_humidity_percent=30.0,
            observation__precipitation_rate_mmh=0.0,
            stability__cape_jkg=0.0,
            stability__lifted_index_c=5.0,
            stability__wind_shear_ms=1.0,
            radar__max_reflectivity_dbz=25.0,
            radar__echo_top_km=4.0,
        )
    )
    stormy_peak = max(stormy.points, key=lambda p: p.thunderstorm_probability)
    calm_peak = max(calm.points, key=lambda p: p.thunderstorm_probability)
    assert stormy_peak.thunderstorm_probability > calm_peak.thunderstorm_probability


def test_confidence_increases_with_more_features():
    sparse = _features(
        observation__temperature_c=None,
        observation__relative_humidity_percent=None,
        observation__precipitation_rate_mmh=None,
        stability__cape_jkg=None,
        stability__lifted_index_c=None,
        stability__wind_shear_ms=None,
        radar__max_reflectivity_dbz=None,
        radar__echo_top_km=None,
        lightning__lightning_density_km2_hr=None,
    )
    full = _features()
    sparse_result = generate_nowcast(sparse)
    full_result = generate_nowcast(full)
    sparse_conf = max(sparse_result.points, key=lambda p: p.confidence).confidence
    full_conf = max(full_result.points, key=lambda p: p.confidence).confidence
    assert full_conf > sparse_conf


def test_risk_timing_fields_present():
    result = generate_nowcast(_features())
    assert result.risk_start_hour is None or 1 <= result.risk_start_hour <= 6
    assert result.risk_end_hour is None or 1 <= result.risk_end_hour <= 6
    assert result.peak_hour is None or 1 <= result.peak_hour <= 6


def test_probabilities_decay_over_longer_horizons():
    result = generate_nowcast(_features())
    first = result.points[0].thunderstorm_probability
    last = result.points[-1].thunderstorm_probability
    assert last <= first


def test_invalid_forecast_time_type_rejected():
    with pytest.raises(TypeError):
        generate_nowcast(_features(), forecast_time="not-a-datetime")  # type: ignore[arg-type]
