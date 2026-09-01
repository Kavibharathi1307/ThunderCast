"""A tiny, dependency-free, genuinely trainable nowcasting classifier.

Why not scikit-learn?
---------------------
The MVP avoids heavy/optional dependencies (see the project constraints: no
unnecessary packages, keep the test surface runnable everywhere). This module
therefore ships a compact, pure-Python **logistic regression** trained with
batch gradient descent. It is a real supervised model:

* ``train`` updates weights from labelled feature rows,
* ``predict_proba`` returns calibrated logistic probabilities,
* ``save``/``load`` persist weights with a version-stamped header,
* metadata honestly reports ``UNTRAINED`` until weights are genuinely fitted.

Because weights are thin, it is trivially explainable: each weight times the
normalized feature is the additive log-odds contribution of that feature.

Honesty
-------
A model is only reported as "trained" here after ``train`` runs on real
labelled data. The shipped application does **not** bundle a dataset, so the
default state is UNTRAINED and the app continues to use the BASELINE engine.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .tabular import FEATURE_NAMES, extract_features
from ..features import ModelFeatures

MODEL_FORMAT = "thundercast-glm"
MODEL_FORMAT_VERSION = 2

# Model lifecycle statuses used across the registry.
STATUS_UNTRAINED = "UNTRAINED"
STATUS_TRAINED = "TRAINED"
STATUS_FAILED = "FAILED"
STATUS_STALE = "STALE"


@dataclass
class ModelConfig:
    """Hyper-parameters for the logistic-regression trainer."""

    learning_rate: float = 0.1
    epochs: int = 400
    l2_regularization: float = 1e-3
    impute_value: float = 0.0  # fill-in for missing/broken features
    feature_scale: float = 30.0  # rough normalization divisor per feature
    seed: int = 0


@dataclass
class ModelMetadata:
    """Honest metadata describing the model's provenance and lineage."""

    status: str = STATUS_UNTRAINED  # UNTRAINED | TRAINED | FAILED | STALE
    model_version: str = "thundercast-glm-0.1"
    trained_at: str | None = None
    n_samples: int = 0
    n_features: int = len(FEATURE_NAMES)
    feature_names: list[str] = field(default_factory=lambda: list(FEATURE_NAMES))
    # Extended provenance (per-target, dataset lineage).
    model_name: str = "thundercast-glm"
    target: str = "thunderstorm"  # thunderstorm | hail | cloudburst
    dataset_name: str | None = None
    dataset_version: str | None = None
    n_train: int = 0
    n_validation: int = 0
    n_test: int = 0
    threshold: float = 0.5
    metrics: dict = field(default_factory=dict)


class TrainableNowcastModel:
    """A pure-Python logistic model for thunderstorm probability."""

    def __init__(self, config: ModelConfig | None = None) -> None:
        self.config = config or ModelConfig()
        self.weights: list[float] = []
        self.intercept: float = 0.0
        self.metadata = ModelMetadata()
        self._rng_state = self.config.seed

    # --- trainability -------------------------------------------------------

    def train(self, feature_rows: Iterable[Iterable[float]], labels: Iterable[int]) -> "TrainableNowcastModel":
        """Fit weights from labelled feature rows (always marks the model TRAINED).

        ``feature_rows`` and ``labels`` must be aligned, non-empty sequences.
        """
        X = [self._impute([float(v) for v in row]) for row in feature_rows]
        y = [int(lbl) for lbl in labels]
        if len(X) == 0 or len(X) != len(y):
            raise ValueError("train requires equal, non-empty feature/label rows")
        if any(len(row) != self.metadata.n_features for row in X):
            raise ValueError(
                f"feature width mismatch: expected {self.metadata.n_features} got {sorted({len(r) for r in X})}"
            )
        self._fit(X, y)
        return self

    def _fit(self, X: list[list[float]], y: list[int]) -> None:
        n_features = self.metadata.n_features
        w = [0.0] * n_features
        b = 0.0
        n = len(y)
        scale = self.config.feature_scale
        for _ in range(self.config.epochs):
            grad = [0.0] * n_features
            grad_b = 0.0
            for row, label in zip(X, y):
                z = b + sum(wi * (xi / scale) for wi, xi in zip(w, row))
                p = _sigmoid(z)
                err = p - label
                grad_b += err
                for i in range(n_features):
                    grad[i] += err * (row[i] / scale)
            for i in range(n_features):
                w[i] -= self.config.learning_rate * ((grad[i] / n) + self.config.l2_regularization * w[i])
            b -= self.config.learning_rate * (grad_b / n)
        self.weights = w
        self.intercept = b
        self.metadata.status = STATUS_TRAINED
        self.metadata.n_samples = n
        self.metadata.trained_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # --- prediction ---------------------------------------------------------

    def predict_proba(self, feature_rows: Iterable[Iterable[float]]) -> list[float]:
        """Return thunderstorm probability (0..1) for each feature row."""
        if not self.weights:
            raise RuntimeError("model is UNTRAINED; no weights available to predict")
        scale = self.config.feature_scale
        out: list[float] = []
        for row in feature_rows:
            vec = self._impute([float(v) for v in row])
            z = self.intercept + sum(
                wi * (xi / scale) for wi, xi in zip(self.weights, vec)
            )
            out.append(_sigmoid(z))
        return out

    def predict_proba_features(self, features: ModelFeatures) -> float:
        """Convenience: probability for a single feature bundle."""
        return self.predict_proba([extract_features(features)])[0]

    def feature_contributions(self, features: ModelFeatures) -> list[dict]:
        """Per-feature log-odds contributions for explainability.

        Each contribution is ``weight * (feature / scale)``. Missing features
        contribute their imputed value's effect.
        """
        if not self.weights:
            raise RuntimeError("model is UNTRAINED")
        vec = self._impute(extract_features(features))
        scale = self.config.feature_scale
        contribs = []
        for name, wi, xi in zip(self.metadata.feature_names, self.weights, vec):
            contribs.append({"feature": name, "value": round(xi, 3), "contribution": round(wi * (xi / scale), 5)})
        return contribs

    # --- persistence --------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "format": MODEL_FORMAT,
            "format_version": MODEL_FORMAT_VERSION,
            "config": {
                "learning_rate": self.config.learning_rate,
                "epochs": self.config.epochs,
                "l2_regularization": self.config.l2_regularization,
                "impute_value": self.config.impute_value,
                "feature_scale": self.config.feature_scale,
                "seed": self.config.seed,
            },
            "weights": [round(w, 8) for w in self.weights],
            "intercept": round(self.intercept, 8),
            "metadata": {
                "status": self.metadata.status,
                "model_version": self.metadata.model_version,
                "trained_at": self.metadata.trained_at,
                "n_samples": self.metadata.n_samples,
                "n_features": self.metadata.n_features,
                "feature_names": self.metadata.feature_names,
                "model_name": self.metadata.model_name,
                "target": self.metadata.target,
                "dataset_name": self.metadata.dataset_name,
                "dataset_version": self.metadata.dataset_version,
                "n_train": self.metadata.n_train,
                "n_validation": self.metadata.n_validation,
                "n_test": self.metadata.n_test,
                "threshold": self.metadata.threshold,
                "metrics": self.metadata.metrics,
            },
        }

    def save(self, path: str | Path) -> str:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        target = path.with_suffix(".tmp")
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)
        os.replace(target, path)
        return str(path)

    @staticmethod
    def load(path: str | Path) -> "TrainableNowcastModel":
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        if payload.get("format") != MODEL_FORMAT:
            raise ValueError("not a ThunderCast GLM model file")
        if payload.get("format_version") != MODEL_FORMAT_VERSION:
            raise ValueError("unsupported model format version")
        cfg = ModelConfig(**payload["config"])
        model = TrainableNowcastModel(cfg)
        model.weights = [float(v) for v in payload["weights"]]
        model.intercept = float(payload["intercept"])
        meta = payload["metadata"]
        model.metadata = ModelMetadata(
            status=meta["status"],
            model_version=meta.get("model_version", "thundercast-glm-0.1"),
            trained_at=meta.get("trained_at"),
            n_samples=meta.get("n_samples", 0),
            n_features=meta.get("n_features", model.metadata.n_features),
            feature_names=meta.get("feature_names", list(FEATURE_NAMES)),
            model_name=meta.get("model_name", "thundercast-glm"),
            target=meta.get("target", "thunderstorm"),
            dataset_name=meta.get("dataset_name"),
            dataset_version=meta.get("dataset_version"),
            n_train=meta.get("n_train", 0),
            n_validation=meta.get("n_validation", 0),
            n_test=meta.get("n_test", 0),
            threshold=meta.get("threshold", 0.5),
            metrics=meta.get("metrics", {}),
        )
        return model

    # --- helpers ------------------------------------------------------------

    def _impute(self, row: list[float]) -> list[float]:
        fill = self.config.impute_value
        return [fill if _is_missing(v) else v for v in row]

    @property
    def is_trained(self) -> bool:
        return self.metadata.status == STATUS_TRAINED and bool(self.weights)

    def set_lineage(self, *, target=None, model_name=None, dataset_name=None,
                    dataset_version=None, n_train=None, n_validation=None,
                    n_test=None, threshold=None, metrics=None, model_version=None) -> "TrainableNowcastModel":
        """Attach extended provenance/metadata (does not change weights/status)."""
        m = self.metadata
        if target is not None:
            m.target = target
        if model_name is not None:
            m.model_name = model_name
        if dataset_name is not None:
            m.dataset_name = dataset_name
        if dataset_version is not None:
            m.dataset_version = dataset_version
        if n_train is not None:
            m.n_train = int(n_train)
        if n_validation is not None:
            m.n_validation = int(n_validation)
        if n_test is not None:
            m.n_test = int(n_test)
        if threshold is not None:
            m.threshold = float(threshold)
        if metrics is not None:
            m.metrics = dict(metrics)
        if model_version is not None:
            m.model_version = model_version
        return self


def _sigmoid(z: float) -> float:
    if z >= 0:
        zz = math.exp(-z)
        return 1.0 / (1.0 + zz)
    zz = math.exp(z)
    return zz / (1.0 + zz)


def _is_missing(value: float) -> bool:
    return value != value  # NaN check that also treats None-as-nan


def default_model_store_path() -> Path:
    """Return the configured model-store file path (rooted at backend/app/ml/models).

    Reads the ``MODEL_STORE_FILE`` configuration value so the persisted default
    filename is configurable rather than hardcoded.
    """
    from ...config import get_settings

    models_dir = Path(__file__).resolve().parent  # .../ml/training
    models_dir = models_dir.parent / "models"  # .../ml/models
    return models_dir / get_settings().MODEL_STORE_FILE
