"""Unit tests for the trained-model manager loader."""

from app.ml.training.manager import load_trained_model
from app.ml.training.model import TrainableNowcastModel, ModelConfig


def test_load_returns_none_when_missing(tmp_path):
    assert load_trained_model(tmp_path / "missing.json") is None


def test_load_returns_model_when_trained(tmp_path):
    n = len(TrainableNowcastModel().metadata.feature_names)
    data = [([30.0] * n, 0), ([95.0] * n, 1), ([28.0] * n, 0), ([93.0] * n, 1)]
    model = TrainableNowcastModel(ModelConfig(epochs=200))
    model.train([row for row, _ in data], [y for _, y in data])
    path = tmp_path / "model.json"
    model.save(path)

    loaded = load_trained_model(path)
    assert loaded is not None
    assert loaded.is_trained is True


def test_load_returns_none_for_untrained_file(tmp_path):
    # Save an untrained model (empty weights) then attempt to load it.
    model = TrainableNowcastModel()
    path = tmp_path / "untrained.json"
    model.save(path)

    assert load_trained_model(path) is None
