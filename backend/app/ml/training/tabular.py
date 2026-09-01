"""Tabular feature extraction for the trainable nowcasting model.

Turns a :class:`ModelFeatures` bundle (and an optional label) into a fixed
row of numeric features that can be fed to a supervised classifier, and back
into the raw feature names for explainability.

Design / honesty
----------------
* Missing values are represented by an explicit imputation fallback inside the
  model (``ModelConfig``), never by silently inventing observations here.
* The extraction is a pure function of the feature bundle so the same code is
  used for training data, live inference and evaluation.
"""

from __future__ import annotations

from typing import Iterable

from ..features import ModelFeatures

# Ordering is authoritative: any change here must be mirrored by a model
# version bump, otherwise persisted weights no longer line up.
FEATURE_NAMES: tuple[str, ...] = (
    "temperature_c",
    "dew_point_c",
    "relative_humidity_percent",
    "pressure_hpa",
    "wind_speed_ms",
    "precipitation_rate_mmh",
    "cloud_cover_percent",
    "cape_jkg",
    "cin_jkg",
    "lifted_index_c",
    "wind_shear_ms",
    "dewpoint_depression_c",
)


class FeatureVectorError(ValueError):
    """Raised when a feature bundle cannot be converted."""


def extract_features(features: ModelFeatures) -> list[float]:
    """Return a fixed-length numeric vector from a feature bundle.

    All values are numeric; missing entries are ``float("nan")`` and are
    imputed by the model layer, not here.
    """
    obs = features.observation
    stab = features.stability
    return [
        _f(obs.temperature_c),
        _f(obs.dew_point_c),
        _f(obs.relative_humidity_percent),
        _f(obs.pressure_hpa),
        _f(obs.wind_speed_ms),
        _f(obs.precipitation_rate_mmh),
        _f(obs.cloud_cover_percent),
        _f(stab.cape_jkg),
        _f(stab.cin_jkg),
        _f(stab.lifted_index_c),
        _f(stab.wind_shear_ms),
        _f(stab.dewpoint_depression_c),
    ]


def _f(value: float | None) -> float:
    if value is None:
        return float("nan")
    return float(value)


def feature_names() -> list[str]:
    return list(FEATURE_NAMES)


def vector_from_rows(rows: Iterable[ModelFeatures]) -> list[list[float]]:
    """Extract a matrix of feature rows from many bundles."""
    return [extract_features(r) for r in rows]
