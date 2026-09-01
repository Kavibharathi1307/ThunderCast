"""Trainable nowcasting model: dataset, tabular features, training pipeline.

This package is the honest boundary between the rule-based BASELINE engine and
a supervised, validated ML model. Without a labelled dataset it reports
UNTRAINED and the application keeps using the baseline engine.
"""

from .dataset import LabelledDataset, LabelledRow, empty_dataset, load_csv
from .tabular import extract_features, feature_names, FEATURE_NAMES
from .model import (
    TrainableNowcastModel,
    ModelConfig,
    ModelMetadata,
    STATUS_UNTRAINED,
    STATUS_TRAINED,
    STATUS_FAILED,
    STATUS_STALE,
)
from .pipeline import (
    train_model,
    train_target_pipeline,
    chronological_split,
    temporal_split,
    TrainResult,
)
from .manager import load_trained_model
from .registry import registry_status, discover_registry, target_model_path, DEFAULT_TARGETS
from .ingest import (
    ingest_raw_csv,
    LabelingSpec,
    DEFAULT_SPECS,
    TARGETS,
    assess_target_availability,
    IngestionReport,
)

__all__ = [
    "LabelledDataset",
    "LabelledRow",
    "empty_dataset",
    "load_csv",
    "extract_features",
    "feature_names",
    "FEATURE_NAMES",
    "TrainableNowcastModel",
    "ModelConfig",
    "ModelMetadata",
    "STATUS_UNTRAINED",
    "STATUS_TRAINED",
    "STATUS_FAILED",
    "STATUS_STALE",
    "train_model",
    "train_target_pipeline",
    "chronological_split",
    "temporal_split",
    "TrainResult",
    "load_trained_model",
    "registry_status",
    "discover_registry",
    "target_model_path",
    "DEFAULT_TARGETS",
    "ingest_raw_csv",
    "LabelingSpec",
    "DEFAULT_SPECS",
    "TARGETS",
    "assess_target_availability",
    "IngestionReport",
]
