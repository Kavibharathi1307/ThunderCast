"""Unit tests for the training pipeline (chronological split) + dataset loader."""

from datetime import datetime, timezone

import pytest

from app.ml.training.dataset import LabelledDataset, LabelledRow, empty_dataset, load_csv
from app.ml.training.pipeline import chronological_split, train_model
from app.ml.features import ModelFeatures


def _ts(index: int) -> datetime:
    import datetime as dt

    return dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(hours=index)


def test_chronological_split_preserves_most_recent_for_validation():
    rows = [LabelledRow(ModelFeatures(latitude=1, longitude=1), i % 2, _ts(i)) for i in range(12)]
    ds = LabelledDataset(rows)
    train_rows, valid_rows = chronological_split(ds, validation_fraction=0.25)
    assert len(train_rows) == 9
    assert len(valid_rows) == 3
    # Validation must be strictly newer (larger index) than every train row.
    assert all(train_row.timestamp < valid_row.timestamp for train_row in train_rows for valid_row in valid_rows)


def test_chronological_split_empty():
    train_rows, valid_rows = chronological_split(empty_dataset())
    assert train_rows == []
    assert valid_rows == []


def test_chronological_split_keeps_at_least_one_train_row():
    rows = [LabelledRow(ModelFeatures(latitude=1, longitude=1), 1, _ts(i)) for i in range(2)]
    train_rows, valid_rows = chronological_split(LabelledDataset(rows), validation_fraction=0.5)
    assert len(train_rows) == 1
    assert len(valid_rows) == 1


def test_train_model_without_dataset_is_honest():
    result = train_model(None)
    assert result.status == "dataset_required"
    assert result.n_samples == 0
    assert result.evaluation is None


def test_train_model_with_dataset_trains_and_evaluates(tmp_path):
    rows = []
    n = 40
    for i in range(n):
        label = 1 if i % 2 == 0 else 0
        rows.append(LabelledRow(_sample_features(label), label, _ts(i)))
    ds = LabelledDataset(rows)
    out = tmp_path / "model.json"
    result = train_model(ds, store_path=out, validation_fraction=0.25)

    assert result.status == "trained"
    assert result.n_train > 0
    assert result.n_validation > 0
    assert result.n_samples == n
    assert out.exists()
    assert result.store_path is not None


def _sample_features(label: int) -> ModelFeatures:
    from app.ml.features import WeatherObservationFeatures, StabilityFeatures

    if label == 1:
        return ModelFeatures(
            latitude=20.0,
            longitude=80.0,
            observation=WeatherObservationFeatures(temperature_c=36.0, relative_humidity_percent=93.0),
            stability=StabilityFeatures(cape_jkg=3000.0),
        )
    return ModelFeatures(
        latitude=20.0,
        longitude=80.0,
        observation=WeatherObservationFeatures(temperature_c=18.0, relative_humidity_percent=30.0),
        stability=StabilityFeatures(cape_jkg=80.0),
    )


def test_load_csv_honours_chronology(tmp_path):
    path = tmp_path / "ds.csv"
    path.write_text(
        "temperature_c,relative_humidity_percent,cape_jkg,timestamp,label\n"
        "30,50,200,2024-01-01T00:00:00Z,0\n"
        "36,90,3000,2024-01-02T00:00:00Z,1\n",
        encoding="utf-8",
    )
    ds = load_csv(path)
    assert len(ds) == 2
    assert ds.n_positive == 1
    assert ds.n_negative == 1
    assert ds.rows[0].timestamp < ds.rows[1].timestamp


def test_load_csv_requires_label_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("temperature_c\n30\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_csv(path)
