"""Unit tests for the evaluation framework (Phase 9)."""

import pytest

from app.ml.evaluation import (
    brier_score,
    evaluate_labelled,
    dataset_status,
    DatasetStatus,
)


def test_dataset_status_is_honest_dataset_required():
    status = dataset_status()
    assert isinstance(status, DatasetStatus)
    assert status.status == "dataset_required"
    assert "dataset" in status.message.lower() or "labelled" in status.message.lower()
    assert "brier" in " ".join(status.available_metrics).lower()
    assert status.n_samples == 0


def test_brier_score_perfect_forecast():
    # Probabilities matching outcomes exactly -> Brier score 0
    score = brier_score([1.0, 0.0, 1.0], [1, 0, 1])
    assert score == pytest.approx(0.0)


def test_brier_score_imperfect_forecast():
    score = brier_score([1.0, 1.0], [1, 0])
    assert score == pytest.approx(0.5)


def test_brier_score_mismatched_lengths_raises():
    with pytest.raises(ValueError):
        brier_score([0.5, 0.5], [1])


def test_brier_score_empty_raises():
    with pytest.raises(ValueError):
        brier_score([], [])


def test_evaluate_labelled_returns_metrics():
    result = evaluate_labelled([0.9, 0.2, 0.7, 0.1, 0.6], [1, 0, 1, 0, 1], threshold=0.5)
    assert 0.0 <= result.brier_score <= 1.0
    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.precision <= 1.0
    assert 0.0 <= result.recall <= 1.0
    assert 0.0 <= result.f1 <= 1.0
    assert result.roc_auc is None or 0.0 <= result.roc_auc <= 1.0
    assert len(result.confusion_matrix) == 2
    assert result.n_samples == 5


def test_evaluate_labelled_perfect_separation():
    result = evaluate_labelled([1.0, 1.0, 0.0, 0.0], [1, 1, 0, 0], threshold=0.5)
    assert result.accuracy == pytest.approx(1.0)
    assert result.precision == pytest.approx(1.0)
    assert result.recall == pytest.approx(1.0)
    assert result.f1 == pytest.approx(1.0)


def test_evaluate_labelled_roc_auc_perfect():
    result = evaluate_labelled([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0], include_roc_auc=True)
    assert result.roc_auc is not None
    assert result.roc_auc >= 0.5


def test_evaluate_labelled_roc_auc_can_be_omitted():
    result = evaluate_labelled([0.9, 0.1], [1, 0], include_roc_auc=False)
    assert result.roc_auc is None
