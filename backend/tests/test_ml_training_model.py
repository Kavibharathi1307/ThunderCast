"""Unit tests for the trainable nowcasting model (Phase: real/trainable)."""

import math

import pytest

from app.ml.training.model import TrainableNowcastModel, ModelConfig, _sigmoid
from app.ml.features import ModelFeatures, WeatherObservationFeatures, StabilityFeatures


def test_model_starts_untrained():
    model = TrainableNowcastModel()
    assert model.metadata.status == "UNTRAINED"
    assert model.is_trained is False


def test_predict_before_training_raises():
    model = TrainableNowcastModel()
    with pytest.raises(RuntimeError):
        model.predict_proba([[1.0] * len(model.metadata.feature_names)])


def test_sigmoid_bounds():
    assert _sigmoid(0.0) == pytest.approx(0.5)
    assert 0.0 < _sigmoid(10.0) < 1.0
    assert 0.0 < _sigmoid(-10.0) < 1.0


def _feature_bundle(moist: float, warm: float, cape: float) -> ModelFeatures:
    return ModelFeatures(
        latitude=20.0,
        longitude=80.0,
        observation=WeatherObservationFeatures(
            temperature_c=warm,
            relative_humidity_percent=moist,
        ),
        stability=StabilityFeatures(cape_jkg=cape),
    )


def test_train_marks_model_trained_and_separates_classes():
    # Consistent separable data: high moisture/temp/CAPE -> positive, low -> negative.
    positives = [
        _feature_bundle(moist=95, warm=36, cape=3000),
        _feature_bundle(moist=92, warm=35, cape=2800),
        _feature_bundle(moist=90, warm=34, cape=2600),
        _feature_bundle(moist=93, warm=36, cape=2900),
        _feature_bundle(moist=91, warm=35, cape=2700),
        _feature_bundle(moist=94, warm=36, cape=3100),
    ]
    negatives = [
        _feature_bundle(moist=30, warm=18, cape=100),
        _feature_bundle(moist=35, warm=17, cape=80),
        _feature_bundle(moist=28, warm=16, cape=50),
        _feature_bundle(moist=32, warm=19, cape=120),
        _feature_bundle(moist=26, warm=15, cape=60),
        _feature_bundle(moist=33, warm=20, cape=90),
    ]
    from app.ml.training.tabular import extract_features

    X = [extract_features(f) for f in positives + negatives]
    y = [1] * len(positives) + [0] * len(negatives)

    model = TrainableNowcastModel(ModelConfig(epochs=800, learning_rate=0.2))
    model.train(X, y)

    assert model.is_trained is True
    assert model.metadata.status == "TRAINED"
    assert model.metadata.n_samples == len(X)

    preds = model.predict_proba(X)
    for p, label in zip(preds, y):
        # Trained on separable/consistent data; probabilities reflect the classes.
        assert 0.0 <= p <= 1.0
    # The average positive probability must beat the average negative probability.
    avg_pos = sum(p for p, lab in zip(preds, y) if lab == 1) / len(positives)
    avg_neg = sum(p for p, lab in zip(preds, y) if lab == 0) / len(negatives)
    assert avg_pos > avg_neg


def test_train_requires_matching_lengths():
    model = TrainableNowcastModel()
    with pytest.raises(ValueError):
        model.train([[1.0] * len(model.metadata.feature_names)], [])


def test_train_rejects_empty():
    model = TrainableNowcastModel()
    with pytest.raises(ValueError):
        model.train([], [])


def test_train_rejects_width_mismatch():
    model = TrainableNowcastModel()
    with pytest.raises(ValueError):
        model.train([[1.0, 2.0]], [0])


def test_feature_contributions_require_trained():
    model = TrainableNowcastModel()
    with pytest.raises(RuntimeError):
        model.feature_contributions(_feature_bundle(50, 25, 100))


def test_save_load_roundtrip(tmp_path):
    # Build a tiny separable dataset over the real feature width.
    n = len(TrainableNowcastModel().metadata.feature_names)
    data = [
        ([30.0] * n, 0),
        ([95.0] * n, 1),
        ([28.0] * n, 0),
        ([93.0] * n, 1),
    ]
    model = TrainableNowcastModel(ModelConfig(epochs=300))
    model.train([row for row, _ in data], [y for _, y in data])

    path = tmp_path / "model.json"
    model.save(path)
    loaded = TrainableNowcastModel.load(path)

    assert loaded.is_trained is True
    assert loaded.metadata.status == "TRAINED"
    assert loaded.metadata.model_version == model.metadata.model_version
    assert loaded.predict_proba([[95.0] * n])[0] > loaded.predict_proba([[30.0] * n])[0]


def test_load_rejects_non_model_file(tmp_path):
    path = tmp_path / "junk.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        TrainableNowcastModel.load(path)
