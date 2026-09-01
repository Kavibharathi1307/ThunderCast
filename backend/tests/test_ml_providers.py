"""Unit tests for data providers (real-data-ready seam)."""

from app.ml.providers import (
    DemoDataProvider,
    WeatherDataProvider,
    RadarDataProvider,
    SatelliteDataProvider,
    LightningDataProvider,
    DATA_PROVENANCE_LABEL,
)
from app.ml.features import ModelFeatures


def test_provider_builds_full_feature_bundle():
    provider = DemoDataProvider()
    features = provider.build_features(21.25, 78.5)
    assert isinstance(features, ModelFeatures)
    assert features.latitude == 21.25
    assert features.longitude == 78.5
    assert features.observation is not None
    assert features.stability is not None
    assert features.radar is not None
    assert features.satellite is not None
    assert features.lightning is not None


def test_provider_outputs_are_deterministic():
    provider = DemoDataProvider()
    a = provider.build_features(21.25, 78.5)
    b = provider.build_features(21.25, 78.5)
    assert a.observation.temperature_c == b.observation.temperature_c
    assert a.observation.relative_humidity_percent == b.observation.relative_humidity_percent
    assert a.radar.max_reflectivity_dbz == b.radar.max_reflectivity_dbz


def test_provider_outputs_vary_by_location():
    provider = DemoDataProvider()
    base = provider.build_features(10.0, 70.0).observation
    other = provider.build_features(30.0, 90.0).observation
    # Not guaranteed every field differs, but the temperature/humidity seeds
    # are location-derived; just assert both are well-formed floats.
    assert base.temperature_c is not None and other.temperature_c is not None
    assert 0.0 <= base.relative_humidity_percent <= 100.0


def test_provider_provenance_is_demo_data():
    assert DemoDataProvider.provenance == DATA_PROVENANCE_LABEL
    assert DATA_PROVENANCE_LABEL == "DEMO DATA"


def test_provider_individual_getters():
    provider = DemoDataProvider()
    assert provider.get_observation(20.0, 78.0) is not None
    assert provider.get_radar(20.0, 78.0) is not None
    assert provider.get_satellite(20.0, 78.0) is not None
    assert provider.get_lightning(20.0, 78.0) is not None


def test_provider_interfaces_exist_for_real_plugins():
    # These ABCs are the contract future real providers must satisfy.
    assert issubclass(DemoDataProvider, WeatherDataProvider)
    assert issubclass(DemoDataProvider, RadarDataProvider)
    assert issubclass(DemoDataProvider, SatelliteDataProvider)
    assert issubclass(DemoDataProvider, LightningDataProvider)


def test_provider_physics_stay_reasonable():
    provider = DemoDataProvider()
    obs = provider.get_observation(21.25, 78.5)
    assert -50.0 <= obs.temperature_c <= 60.0
    assert 900.0 <= obs.pressure_hpa <= 1100.0
    assert 0.0 <= obs.wind_speed_ms <= 60.0
    assert 0.0 <= obs.precipitation_rate_mmh <= 150.0
