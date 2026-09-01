"""Model evaluation framework.

Provides probabilistic-nowcasting metrics (Brier score, calibration,
classification metrics when a threshold is applied).

Honesty / Phase 9
-----------------
There is **no labelled meteorological dataset** in this MVP, so evaluation
cannot and must not fabricate real scores. The framework therefore exposes:

* evaluation-ready metrics functions (usable when a dataset is plugged in)
* a `DatasetStatus` API that returns an honest ``dataset_required`` status
  and clear message until a real labelled dataset is supplied.

Callers should never report evaluation scores derived from demo data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

DEFAULT_THRESHOLD = 0.5


@dataclass
class DatasetStatus:
    """Honest report of whether evaluation can run."""

    status: str  # "dataset_required" | "ready"
    message: str
    n_samples: int = 0
    available_metrics: list[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Full evaluation metrics from a labelled (prob, label) dataset."""

    brier_score: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    confusion_matrix: list[list[int]]
    n_samples: int

    def as_dict(self) -> dict:
        return {
            "brier_score": self.brier_score,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "confusion_matrix": self.confusion_matrix,
            "n_samples": self.n_samples,
        }


def brier_score(y_prob: Iterable[float], y_true: Iterable[int]) -> float:
    """Compute the Brier score (mean squared probability error)."""
    probs = list(y_prob)
    y = list(y_true)
    if len(probs) != len(y) or not probs:
        raise ValueError("y_prob and y_true must be same length and non-empty")
    return sum((p - t) ** 2 for p, t in zip(probs, y)) / len(probs)


def _classification_metrics(y_prob: Iterable[float], y_true: Iterable[int], threshold: float = DEFAULT_THRESHOLD):
    """Helper to build classification metrics from probability + label."""
    probs = list(y_prob)
    y = list(y_true)
    preds = [1 if p >= threshold else 0 for p in probs]
    n = len(y)
    tp = sum(1 for p, t in zip(preds, y) if p == 1 and t == 1)
    fp = sum(1 for p, t in zip(preds, y) if p == 1 and t == 0)
    tn = sum(1 for p, t in zip(preds, y) if p == 0 and t == 0)
    fn = sum(1 for p, t in zip(preds, y) if p == 0 and t == 1)

    accuracy = (tp + tn) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": [[tn, fp], [fn, tp]],
    }


def evaluate_labelled(
    y_prob: Iterable[float],
    y_true: Iterable[int],
    threshold: float = DEFAULT_THRESHOLD,
    include_roc_auc: bool = True,
) -> EvaluationResult:
    """Compute full metrics from a real labelled (prob, label) dataset.

    Only call this with genuine labelled observations, never demo data.
    """
    probs = list(y_prob)
    y = list(y_true)
    bs = brier_score(probs, y)
    cm_metrics = _classification_metrics(probs, y, threshold)
    roc_auc = None
    if include_roc_auc:
        roc_auc = _trapezoidal_roc_auc(probs, y)
    return EvaluationResult(
        brier_score=round(bs, 4),
        accuracy=round(cm_metrics["accuracy"], 4),
        precision=round(cm_metrics["precision"], 4),
        recall=round(cm_metrics["recall"], 4),
        f1=round(cm_metrics["f1"], 4),
        roc_auc=round(roc_auc, 4) if roc_auc is not None else None,
        confusion_matrix=cm_metrics["confusion_matrix"],
        n_samples=len(y),
    )


def evaluate_baseline(
    y_true: Iterable[int],
    baseline_prob: float | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> EvaluationResult:
    """Evaluate a naive baseline (climatology or majority-class).

    If ``baseline_prob`` is None, the majority-class probability is used (the
    empirical base rate rounded toward the majority class). This gives a
    meaningful reference point for skill assessment.
    """
    y = list(y_true)
    if not y:
        raise ValueError("y_true must be non-empty")
    rate = sum(y) / len(y)
    prob = baseline_prob if baseline_prob is not None else (rate if rate >= 0.5 else 1.0 - rate)
    return evaluate_labelled([prob] * len(y), y, threshold=threshold)


def inspect_calibration(
    y_prob: Iterable[float],
    y_true: Iterable[int],
    n_bins: int = 10,
    min_bin_size: int = 5,
) -> dict:
    """Inspect probabilistic calibration using reliability bins.

    Splits predictions into probability bins and compares the mean predicted
    probability with the observed event frequency per bin. Returns per-bin data
    and an overall reliability error.

    Returns a low-confidence result when the sample is too small to be
    meaningful, so callers never claim calibration without evidence.
    """
    probs = list(y_prob)
    y = list(y_true)
    if len(probs) != len(y) or len(probs) == 0:
        return {"reliable": False, "n_bins": 0, "reason": "no data"}
    if len(probs) < min_bin_size * 2:
        return {
            "reliable": False,
            "n_bins": 0,
            "reason": f"too few samples ({len(probs)}) for calibration inspection",
        }
    edge = 1.0 / n_bins
    bins = [[] for _ in range(n_bins)]
    for p, t in zip(probs, y):
        idx = min(int(p / edge), n_bins - 1)
        bins[idx].append((p, t))
    reliability = []
    n_used = 0
    for i, bin_rows in enumerate(bins):
        if not bin_rows:
            continue
        n = len(bin_rows)
        if n < min_bin_size:
            continue
        mean_pred = sum(p for p, _ in bin_rows) / n
        obs_freq = sum(t for _, t in bin_rows) / n
        reliability.append(
            {
                "bin": i,
                "range_low": round(i * edge, 3),
                "range_high": round((i + 1) * edge, 3),
                "n": n,
                "mean_predicted": round(mean_pred, 4),
                "observed_frequency": round(obs_freq, 4),
            }
        )
        n_used += n
    if not reliability:
        return {
            "reliable": False,
            "n_bins": 0,
            "reason": "no bin had enough samples",
        }
    mae = sum(abs(b["mean_predicted"] - b["observed_frequency"]) for b in reliability) / len(reliability)
    return {
        "reliable": mae <= 0.15,
        "mean_absolute_calibration_error": round(mae, 4),
        "n_bins_used": len(reliability),
        "n_samples_used": n_used,
        "bins": reliability,
    }


def dataset_status() -> DatasetStatus:
    """Report the (honest) evaluation readiness of the MVP.

    Returns ``dataset_required`` because no real labelled meteorological
    dataset is bundled. A real dataset can be plugged in later to enable
    :func:`evaluate_labelled`.
    """
    return DatasetStatus(
        status="dataset_required",
        message=(
            "Model evaluation requires labelled meteorological observations. "
            "No real dataset is bundled in this MVP, so no evaluation scores "
            "are reported. Provide a labelled dataset to enable "
            "Brier score, calibration and classification metrics."
        ),
        n_samples=0,
        available_metrics=["brier_score", "accuracy", "precision", "recall", "f1", "roc_auc"],
    )


def _trapezoidal_roc_auc(y_prob: list[float], y_true: list[int]) -> float:
    """Trapezoidal ROC-AUC from probability + binary labels."""
    pairs = sorted(zip(y_prob, y_true), key=lambda x: x[0], reverse=True)
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    tpr = 0.0
    fpr = 0.0
    auc = 0.0
    prev_tpr = 0.0
    prev_fpr = 0.0
    for i, (_, t) in enumerate(pairs):
        if t == 1:
            tpr += 1.0 / n_pos
        else:
            fpr += 1.0 / n_neg
            auc += (prev_tpr + tpr) / 2.0 * (fpr - prev_fpr)
            prev_tpr = tpr
            prev_fpr = fpr
    return auc
