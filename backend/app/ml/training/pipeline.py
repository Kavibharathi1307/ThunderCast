"""Training + chronological-validation pipeline for the trainable model.

Responsibilities
----------------
* Split a labelled dataset **chronologically** (train on the oldest period,
  validate on the middle, test on the newest) so all evaluation reflects
  temporal generalisation rather than a random shuffle that leaks the future.
* Train the pure-Python logistic model on the training split, per target.
* Evaluate on validation **and** held-out test using Brier score, ROC-AUC and
  classification metrics, plus a climatology/majority baseline comparison.
* Persist the trained model with full lineage metadata.

Honesty
-------
* If no labelled data exists (or the split is too small), the pipeline returns
  ``dataset_insufficient`` / ``dataset_required`` instead of inventing metrics.
* A target whose label field is missing is reported as "unavailable" and is not
  trained; it is never silently dropped or hallucinated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..evaluation import EvaluationResult, evaluate_labelled, evaluate_baseline, inspect_calibration
from .dataset import LabelledDataset, LabelledRow
from .model import (
    TrainableNowcastModel,
    ModelConfig,
    default_model_store_path,
    STATUS_UNTRAINED,
)
from .tabular import extract_features, feature_names

DEFAULT_THRESHOLD = 0.5


@dataclass
class TrainResult:
    """Outcome of a training run (honest even when no data was available)."""

    status: str  # "trained" | "dataset_required" | "dataset_insufficient"
    message: str
    target: str = "thunderstorm"
    n_samples: int = 0
    n_train: int = 0
    n_validation: int = 0
    n_test: int = 0
    model_version: str = "thundercast-glm-0.1"
    evaluation: EvaluationResult | None = None          # validation-set metrics
    test_evaluation: EvaluationResult | None = None     # held-out test metrics
    baseline_climatology: float | None = None
    baseline_comparison: dict | None = None
    calibration: dict | None = None
    store_path: str | None = None


def chronological_split(
    dataset: LabelledDataset, validation_fraction: float = 0.25
) -> tuple[list[LabelledRow], list[LabelledRow]]:
    """Split a chronology-sorted dataset into train/validation (2-way).

    The most recent ``validation_fraction`` of rows form the validation set;
    everything older is training. Kept for backward compatibility.
    """
    rows = dataset.rows
    n = len(rows)
    if n == 0:
        return [], []
    n_validation = max(1, int(round(n * validation_fraction)))
    n_validation = min(n_validation, n - 1)
    split_at = n - n_validation
    return rows[:split_at], rows[split_at:]


def temporal_split(
    dataset: LabelledDataset,
    validation_fraction: float = 0.15,
    test_fraction: float = 0.15,
) -> tuple[list[LabelledRow], list[LabelledRow], list[LabelledRow]]:
    """Chronological 3-way split into train / validation / test.

    earliest ──► TRAIN ──► VALIDATION ──► TEST ──► latest

    The validation and test windows are the MOST RECENT data; training uses only
    earlier data. This prevents future leakage into training and gives a true
    temporal out-of-sample test.
    """
    rows = dataset.rows
    n = len(rows)
    if n == 0:
        return [], [], []
    n_test = max(1, int(round(n * test_fraction)))
    n_val = max(1, int(round(n * validation_fraction)))
    # Reserve at least one training row.
    reserved = n_test + n_val
    if reserved >= n:
        n_test = max(1, n // 3)
        n_val = max(1, n // 3)
        if n_test + n_val >= n:
            n_test = 1
            n_val = 1
    split_val = n - n_test - n_val
    split_test = n - n_test
    train = rows[:split_val]
    validation = rows[split_val:split_test]
    test = rows[split_test:]
    return train, validation, test


def _sufficient_for_training(train: list[LabelledRow], minimum_train: int = 20) -> bool:
    if len(train) < minimum_train:
        return False
    n_pos = sum(1 for r in train if r.label == 1)
    n_neg = sum(1 for r in train if r.label == 0)
    return n_pos >= 1 and n_neg >= 1


def train_model(
    dataset: LabelledDataset | None,
    *,
    config: ModelConfig | None = None,
    validation_fraction: float = 0.25,
    store_path: str | Path | None = None,
    target: str = "thunderstorm",
    dataset_name: str | None = None,
    dataset_version: str | None = None,
) -> TrainResult:
    """Train and evaluate a single-target model.

    Backward-compatible: validates on the validation split and returns honest
    status when no/sufficient data is missing.
    """
    dataset = dataset or LabelledDataset([])
    if len(dataset) == 0:
        return TrainResult(
            status="dataset_required",
            message=(
                "No labelled meteorological dataset is available. Provide one "
                "to train and validate the nowcasting model; the app remains on "
                "the BASELINE engine until then."
            ),
            target=target,
            n_samples=0,
            model_version="thundercast-glm-0.1",
        )

    train_rows, valid_rows = chronological_split(dataset, validation_fraction)
    if not _sufficient_for_training(train_rows):
        return TrainResult(
            status="dataset_insufficient",
            message=(
                "Dataset is present but too small or single-class to form a "
                "valid training split. No metrics are reported."
            ),
            target=target,
            n_samples=len(dataset),
            n_train=len(train_rows),
            n_validation=len(valid_rows),
            model_version="thundercast-glm-0.1",
        )

    model = TrainableNowcastModel(config or ModelConfig())
    model.train(
        (extract_features(r.features) for r in train_rows),
        (r.label for r in train_rows),
    )

    evaluation: EvaluationResult | None = None
    if valid_rows:
        probs = model.predict_proba(extract_features(r.features) for r in valid_rows)
        evaluation = evaluate_labelled(probs, [r.label for r in valid_rows])

    path = Path(store_path) if store_path else default_model_store_path()
    model.set_lineage(
        target=target,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        n_train=len(train_rows),
        n_validation=len(valid_rows),
        n_test=0,
        threshold=DEFAULT_THRESHOLD,
        metrics=evaluation.as_dict() if evaluation else {},
    )
    model.save(path)

    return TrainResult(
        status="trained",
        message="Trained on the provided labelled dataset with chronological validation.",
        target=target,
        n_samples=len(dataset),
        n_train=len(train_rows),
        n_validation=len(valid_rows),
        n_test=0,
        model_version=model.metadata.model_version,
        evaluation=evaluation,
        store_path=str(path),
    )


def train_target_pipeline(
    dataset: LabelledDataset | None,
    *,
    target: str = "thunderstorm",
    config: ModelConfig | None = None,
    validation_fraction: float = 0.15,
    test_fraction: float = 0.15,
    store_path: str | Path | None = None,
    dataset_name: str | None = None,
    dataset_version: str | None = None,
) -> TrainResult:
    """Train + validate + test one target with a temporal split.

    Reports test-set metrics (Brier, ROC-AUC, P/R/F1, CM), a climatology
    baseline comparison, and a calibration inspection. Returns
    ``dataset_insufficient`` when the split cannot support honest evaluation.
    """
    dataset = dataset or LabelledDataset([])
    if len(dataset) == 0:
        return TrainResult(
            status="dataset_required",
            message="No labelled meteorological dataset is available; the model remains UNTRAINED.",
            target=target,
            n_samples=0,
            model_version="thundercast-glm-0.1",
        )

    train_rows, valid_rows, test_rows = temporal_split(
        dataset, validation_fraction, test_fraction
    )
    if not _sufficient_for_training(train_rows) or not test_rows or not valid_rows:
        return TrainResult(
            status="dataset_insufficient",
            message=(
                "Dataset is present but too small (or single-class) to support "
                "a valid temporal train/validation/test split. No metrics are "
                "reported; the model remains UNTRAINED."
            ),
            target=target,
            n_samples=len(dataset),
            n_train=len(train_rows),
            n_validation=len(valid_rows),
            n_test=len(test_rows),
            model_version="thundercast-glm-0.1",
        )

    model = TrainableNowcastModel(config or ModelConfig())
    model.train(
        (extract_features(r.features) for r in train_rows),
        (r.label for r in train_rows),
    )

    evaluation = None
    if valid_rows:
        probs = model.predict_proba(extract_features(r.features) for r in valid_rows)
        evaluation = evaluate_labelled(probs, [r.label for r in valid_rows])

    test_evaluation = None
    if test_rows:
        test_probs = model.predict_proba(extract_features(r.features) for r in test_rows)
        test_evaluation = evaluate_labelled(test_probs, [r.label for r in test_rows])

    baseline_climatology = None
    baseline_comparison = None
    if test_rows:
        y_test = [r.label for r in test_rows]
        climatology = sum(y_test) / len(y_test)
        baseline_climatology = round(climatology, 4)
        # Climatology / majority baseline: predict the majority class probability.
        majority_prob = climatology if climatology >= 0.5 else (1.0 - climatology)
        baseline_eval = evaluate_labelled([majority_prob] * len(y_test), y_test)
        baseline_comparison = {
            "climatology_rate": baseline_climatology,
            "baseline_brier": baseline_eval.brier_score,
            "baseline_accuracy": baseline_eval.accuracy,
            "model_brier": test_evaluation.brier_score,
            "model_accuracy": test_evaluation.accuracy,
            "brier_skill_over_baseline": round(
                (baseline_eval.brier_score - test_evaluation.brier_score), 4
            ),
        }

    calibration = inspect_calibration(test_probs, y_test) if test_rows else None

    path = Path(store_path) if store_path else default_model_store_path()
    model.set_lineage(
        target=target,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        n_train=len(train_rows),
        n_validation=len(valid_rows),
        n_test=len(test_rows),
        threshold=DEFAULT_THRESHOLD,
        metrics=(test_evaluation.as_dict() if test_evaluation else {}),
    )
    model.save(path)

    return TrainResult(
        status="trained",
        message=(
            "Trained with chronological train/validation/test splitting and "
            "honest out-of-sample evaluation."
        ),
        target=target,
        n_samples=len(dataset),
        n_train=len(train_rows),
        n_validation=len(valid_rows),
        n_test=len(test_rows),
        model_version=model.metadata.model_version,
        evaluation=evaluation,
        test_evaluation=test_evaluation,
        baseline_climatology=baseline_climatology,
        baseline_comparison=baseline_comparison,
        calibration=calibration,
        store_path=str(path),
    )
