"""Unit tests for the prototype impact model."""

from app.ml.impacts import assess_impacts, ImpactResult, IMPACT_CATEGORIES
from app.ml.features import (
    ModelFeatures,
    WeatherObservationFeatures,
    StabilityFeatures,
    RadarFeatures,
    SatelliteFeatures,
    LightningFeatures,
)
from app.ml.predictor import generate_nowcast


def _features(**overrides) -> ModelFeatures:
    base = ModelFeatures(
        latitude=21.25,
        longitude=78.5,
        observation=WeatherObservationFeatures(
            temperature_c=32.0,
            relative_humidity_percent=85.0,
            precipitation_rate_mmh=40.0,
            cloud_cover_percent=90.0,
        ),
        stability=StabilityFeatures(cape_jkg=2200.0, wind_shear_ms=22.0),
        radar=RadarFeatures(max_reflectivity_dbz=60.0),
        satellite=SatelliteFeatures(cloud_top_temperature_k=200.0),
        lightning=LightningFeatures(lightning_density_km2_hr=4.0),
    )
    if overrides:
        obs = base.observation
        stab = base.stability
        rad = base.radar
        ltg = base.lightning
        for key, value in overrides.items():
            for obj, name in (
                (obs, "observation"),
                (stab, "stability"),
                (rad, "radar"),
                (ltg, "lightning"),
            ):
                if key.startswith(name + "__"):
                    setattr(obj, key.split("__", 1)[1], value)
                    break
    return base


def test_impact_categories_included():
    impacts = assess_impacts(_features())
    assert isinstance(impacts, ImpactResult)
    for category in IMPACT_CATEGORIES:
        score = getattr(impacts, category)
        assert 0.0 <= score <= 1.0


def test_all_impact_scores_bounded():
    impacts = assess_impacts(_features())
    for value in impacts.as_dict().values():
        assert 0.0 <= value <= 1.0


def test_high_rain_increases_flooding_and_waterlogging():
    wet = assess_impacts(_features(observation__precipitation_rate_mmh=80.0, observation__relative_humidity_percent=95.0))
    dry = assess_impacts(_features(observation__precipitation_rate_mmh=1.0, observation__relative_humidity_percent=40.0))
    assert wet.flooding > dry.flooding
    assert wet.waterlogging > dry.waterlogging


def test_high_lightning_increases_lightning_impact():
    active = assess_impacts(_features(lightning__lightning_density_km2_hr=8.0))
    quiet = assess_impacts(_features(lightning__lightning_density_km2_hr=0.0))
    assert active.lightning > quiet.lightning


def test_high_reflectivity_increases_hail_impact():
    strong = assess_impacts(_features(radar__max_reflectivity_dbz=70.0))
    weak = assess_impacts(_features(radar__max_reflectivity_dbz=25.0))
    assert strong.hail > weak.hail


def test_impact_label_marked_as_prototype():
    impacts = assess_impacts(_features())
    assert impacts.label == "PROTOTYPE IMPACT MODEL"


def test_impacts_respect_nowcast_peak():
    features = _features()
    nowcast = generate_nowcast(features)
    impacts = assess_impacts(features, nowcast)
    assert 0.0 <= impacts.lightning <= 1.0
    assert impacts.as_dict()  # non-empty

def test_visibility_rises_with_precipitation_and_cloud():
    stormy = assess_impacts(_features(observation__precipitation_rate_mmh=70.0, observation__cloud_cover_percent=100.0))
    clear = assess_impacts(_features(observation__precipitation_rate_mmh=0.0, observation__cloud_cover_percent=10.0))
    assert stormy.visibility > clear.visibility
