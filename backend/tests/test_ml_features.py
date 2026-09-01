"""Unit tests for the feature-engineering layer."""

from app.ml.features import (
    ModelFeatures,
    WeatherObservationFeatures,
    StabilityFeatures,
    RadarFeatures,
    SatelliteFeatures,
    LightningFeatures,
    derived_relative_humidity,
)


def test_feature_bundle_defaults_to_unknown():
    mf = ModelFeatures(latitude=20.0, longitude=78.0)
    assert mf.observation.temperature_c is None
    assert mf.stability.cape_jkg is None
    assert mf.radar.max_reflectivity_dbz is None
    assert mf.satellite.cloud_top_temperature_k is None
    assert mf.lightning.lightning_density_km2_hr is None


def test_feature_bundle_carries_coordinates():
    mf = ModelFeatures(latitude=12.5, longitude=77.5)
    assert mf.latitude == 12.5
    assert mf.longitude == 77.5


def test_observation_features_optionally_populated():
    obs = WeatherObservationFeatures(
        temperature_c=30.0,
        dew_point_c=24.0,
        relative_humidity_percent=68.0,
        pressure_hpa=1005.0,
        wind_speed_ms=6.0,
        wind_direction_deg=200.0,
        precipitation_mm=5.0,
        precipitation_rate_mmh=12.0,
        cloud_cover_percent=80.0,
    )
    assert obs.temperature_c == 30.0
    assert obs.precipitation_rate_mmh == 12.0


def test_derived_relative_humidity_magnus():
    # Saturated air: dew point == temperature -> ~100% RH
    rh = derived_relative_humidity(30.0, 30.0)
    assert rh is not None
    assert 90.0 <= rh <= 100.0
    # Dry air: large dewpoint depression -> low RH
    rh_dry = derived_relative_humidity(30.0, 10.0)
    assert rh_dry is not None
    assert rh_dry < rh


def test_derived_relative_humidity_bounded():
    rh = derived_relative_humidity(45.0, 43.0)
    assert 0.0 <= rh <= 100.0


def test_derived_relative_humidity_missing_inputs_returns_none():
    assert derived_relative_humidity(None, 20.0) is None
    assert derived_relative_humidity(20.0, None) is None
    assert derived_relative_humidity(None, None) is None


def test_stability_radar_satellite_lightning_population():
    stab = StabilityFeatures(cape_jkg=1500.0, cin_jkg=50.0, lifted_index_c=-3.0, wind_shear_ms=15.0)
    rad = RadarFeatures(max_reflectivity_dbz=45.0, echo_top_km=10.0)
    sat = SatelliteFeatures(cloud_top_temperature_k=210.0, cloud_top_pressure_hpa=350.0)
    ltg = LightningFeatures(lightning_density_km2_hr=2.5)
    assert stab.cape_jkg == 1500.0
    assert stab.cin_jkg == 50.0
    assert rad.max_reflectivity_dbz == 45.0
    assert sat.cloud_top_pressure_hpa == 350.0
    assert ltg.lightning_density_km2_hr == 2.5
