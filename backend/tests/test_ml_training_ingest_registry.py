"""Unit tests for ingestion, registry, and the per-target temporal pipeline."""

from datetime import datetime, timezone

import pytest

from app.ml.evaluation import (
    EvaluationResult,
    evaluate_baseline,
    inspect_calibration,
)
from app.ml.features import ModelFeatures, WeatherObservationFeatures, StabilityFeatures
from app.ml.training.dataset import LabelledDataset, LabelledRow, empty_dataset
from app.ml.training.ingest import (
    DEFAULT_SPECS,
    LabelingSpec,
    assess_target_availability,
    ingest_raw_csv,
)
from app.ml.training.model import (
    TrainableNowcastModel,
    ModelConfig,
    STATUS_UNTRAINED,
    STATUS_TRAINED,
    STATUS_FAILED,
    STATUS_STALE,
)
from app.ml.training.pipeline import temporal_split, train_target_pipeline


def _ts(index: int) -> datetime:
    import datetime as dt

    return dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(hours=index)


def _sample_features(label: int) -> ModelFeatures:
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


# ---------------------------------------------------------------------------
# temporal_split
# ---------------------------------------------------------------------------


def test_temporal_split_is_strictly_chronological():
    rows = [LabelledRow(_sample_features(i % 2), i % 2, _ts(i)) for i in range(120)]
    train_rows, valid_rows, test_rows = temporal_split(
        LabelledDataset(rows), validation_fraction=0.15, test_fraction=0.15
    )
    assert len(train_rows) > 0
    assert len(valid_rows) > 0
    assert len(test_rows) > 0
    assert len(train_rows) + len(valid_rows) + len(test_rows) == 120
    # Oldest ╮  train  />  validation  />  test  (strictly increasing times)
    assert all(a.timestamp < b.timestamp for a in train_rows for b in valid_rows)
    assert all(a.timestamp < b.timestamp for a in valid_rows for b in test_rows)


def test_temporal_split_empty():
    t, v, te = temporal_split(empty_dataset())
    assert t == [] and v == [] and te == []


def test_temporal_split_small_reserves_all_three_sets():
    rows = [LabelledRow(_sample_features(1), 1, _ts(i)) for i in range(6)]
    t, v, te = temporal_split(LabelledDataset(rows), validation_fraction=0.15, test_fraction=0.15)
    assert t and v and te


# ---------------------------------------------------------------------------
# ingestion
# ---------------------------------------------------------------------------


def test_ingest_raw_csv_thunderstorm_via_event_type(tmp_path):
    path = tmp_path / "events.csv"
    path.write_text(
        "timestamp,EVENT_TYPE,temperature_c,relative_humidity_percent\n"
        "2024-01-01T00:00:00Z,THUNDERSTORM WIND,36,90\n"
        "2024-01-01T01:00:00Z,HEAVY RAIN,30,70\n"
        "2024-01-01T02:00:00Z,HAIL,30,70\n",
        encoding="utf-8",
    )
    dataset, report = ingest_raw_csv(path, "thunderstorm")
    assert dataset is not None
    assert report.available is True
    assert report.rows_ingested == 3
    assert report.n_positive == 1
    assert report.n_negative == 2
    assert dataset.target == "thunderstorm"
    assert dataset.rows[0].target == "thunderstorm"


def test_ingest_raw_csv_unavailable_when_event_field_missing(tmp_path):
    path = tmp_path / "no_events.csv"
    path.write_text(
        "timestamp,temperature_c,relative_humidity_percent\n"
        "2024-01-01T00:00:00Z,30,60\n",
        encoding="utf-8",
    )
    dataset, report = ingest_raw_csv(path, "hail")
    assert dataset is None
    assert report.available is False
    assert "unavailable" in report.message.lower()


def test_ingest_raw_csv_skips_malformed_numeric_rows(tmp_path):
    path = tmp_path / "bad_nums.csv"
    path.write_text(
        "timestamp,EVENT_TYPE,temperature_c\n"
        "2024-01-01T00:00:00Z,HEAVY RAIN,36\n"
        "2024-01-01T01:00:00Z,THUNDERSTORM WIND,not-a-number\n"
        "2024-01-01T02:00:00Z,HAIL,25\n",
        encoding="utf-8",
    )
    dataset, report = ingest_raw_csv(path, "cloudburst")
    assert dataset is not None
    # Non-numeric features are coerced to None (then imputed), never an error.
    assert report.rows_ingested == 3
    assert report.skipped_bad_value == 0


def test_ingest_raw_csv_unknown_target_rejected(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("timestamp,EVENT_TYPE\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ingest_raw_csv(path, "blizzard")


def test_assess_target_availability():
    available, unavailable = assess_target_availability(["EVENT_TYPE", "timestamp"])
    assert "thunderstorm" in available
    assert "hail" in available
    assert "cloudburst" in available
    assert unavailable == []


def test_threshold_spec_labels_high_precip():
    spec = LabelingSpec(target="cloudburst", value_field="precipitation_mm", threshold=15.0, operator=">=")
    from app.ml.training.ingest import _spec_label

    assert _spec_label(spec, {"precipitation_mm": "20"}) == 1
    assert _spec_label(spec, {"precipitation_mm": "10"}) == 0
    assert _spec_label(spec, {"precipitation_mm": ""}) is None


# ---------------------------------------------------------------------------
# train_target_pipeline
# ---------------------------------------------------------------------------


def test_train_target_pipeline_small_is_honest_insufficient():
    rows = [LabelledRow(_sample_features(1), 1, _ts(i)) for i in range(4)]
    result = train_target_pipeline(LabelledDataset(rows), store_path="ignored.json")
    assert result.status == "dataset_insufficient"
    assert result.test_evaluation is None
    assert result.baseline_climatology is None


def test_train_target_pipeline_no_data_is_honest_required():
    result = train_target_pipeline(None)
    assert result.status == "dataset_required"
    assert result.n_samples == 0


def test_train_target_pipeline_trains_and_reports_test_metrics(tmp_path):
    n = 200
    rows = [LabelledRow(_sample_features(i % 2), i % 2, _ts(i)) for i in range(n)]
    ds = LabelledDataset(rows, target="thunderstorm")
    out = tmp_path / "thundercast_model_thunderstorm.json"
    result = train_target_pipeline(
        ds,
        target="thunderstorm",
        store_path=out,
        dataset_name="ncei-test",
        dataset_version="v1",
    )

    assert result.status == "trained"
    assert result.n_samples == n
    assert result.n_train > 0
    assert result.n_validation > 0
    assert result.n_test > 0
    assert result.test_evaluation is not None
    assert 0.0 <= result.test_evaluation.brier_score <= 1.0
    assert result.test_evaluation.n_samples == result.n_test
    assert result.baseline_climatology is not None
    assert result.baseline_comparison is not None
    assert "brier_skill_over_baseline" in result.baseline_comparison
    assert out.exists()


# ---------------------------------------------------------------------------
# model metadata / registry
# ---------------------------------------------------------------------------


def test_model_metadata_roundtrip_extended_fields(tmp_path):
    m = TrainableNowcastModel()
    m.train(
        ([0.0] * m.metadata.n_features for _ in range(20)),
        [i % 2 for i in range(20)],
    )
    m.set_lineage(
        target="hail",
        dataset_name="ncei-raw",
        dataset_version="2024",
        n_train=20,
        n_validation=6,
        n_test=6,
        threshold=0.4,
        metrics={"brier_score": 0.2},
    )
    path = tmp_path / "thundercast_model_hail.json"
    m.save(path)
    loaded = TrainableNowcastModel.load(path)
    assert loaded.metadata.status == STATUS_TRAINED
    assert loaded.metadata.target == "hail"
    assert loaded.metadata.dataset_name == "ncei-raw"
    assert loaded.metadata.dataset_version == "2024"
    assert loaded.metadata.n_train == 20
    assert loaded.metadata.n_validation == 6
    assert loaded.metadata.n_test == 6
    assert loaded.metadata.threshold == 0.4
    assert loaded.metadata.metrics == {"brier_score": 0.2}
    assert loaded.is_trained


def test_registry_reports_untrained_without_artifacts():
    from app.ml.training.registry import registry_status

    status = registry_status()
    assert status["any_trained"] is False
    for target in ("thunderstorm", "hail", "cloudburst"):
        assert status["artifacts"][target]["status"] == STATUS_UNTRAINED


def test_mark_status_validation():
    from app.ml.training.registry import mark_status

    m = TrainableNowcastModel()
    mark_status(m, STATUS_STALE)
    assert m.metadata.status == STATUS_STALE
    with pytest.raises(ValueError):
        mark_status(m, "BOGUS")


def test_registry_discovers_trained_artifact(tmp_path):
    from app.ml.training.registry import discover_registry

    m = TrainableNowcastModel()
    m.train(
        ([0.0] * m.metadata.n_features for _ in range(20)),
        [i % 2 for i in range(20)],
    )
    m.set_lineage(target="hail", dataset_name="ncei", n_train=20)
    path = tmp_path / "thundercast_model_hail.json"
    m.save(path)
    entries = discover_registry(tmp_path)
    assert "hail" in entries
    assert entries["hail"]["status"] == STATUS_TRAINED
    assert entries["hail"]["dataset_name"] == "ncei"


# ---------------------------------------------------------------------------
# evaluation helpers
# ---------------------------------------------------------------------------


def test_evaluate_baseline_majority_class():
    y = [1, 1, 1, 0, 0, 0, 0]
    result = evaluate_baseline(y)
    assert isinstance(result, EvaluationResult)
    assert 0.0 <= result.accuracy <= 1.0


def test_inspect_calibration_too_few_samples_is_not_reliable():
    probs = [0.2, 0.6, 0.9]
    y = [0, 1, 1]
    result = inspect_calibration(probs, y, min_bin_size=5)
    assert result["reliable"] is False
    assert "too few samples" in result["reason"]


def test_inspect_calibration_good_reliability():
    probs = [0.9] * 20 + [0.1] * 20
    y = [1] * 20 + [0] * 20
    result = inspect_calibration(probs, y, n_bins=10, min_bin_size=5)
    assert result["reliable"] is True
    assert result["mean_absolute_calibration_error"] <= 0.15
