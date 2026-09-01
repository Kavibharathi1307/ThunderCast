"""Model registry: manages per-target model artifacts and lifecycle status.

The registry understands the model's **lifecycle**:

* ``UNTRAINED`` — no genuine labelled data has been used; no weights exist.
* ``TRAINED``  — a genuine model file exists with weights fitted on real data.
* ``FAILED``   — a training/ingestion attempt errored or produced an invalid model.
* ``STALE``    — a fitted model whose dataset lineage is obsolete/no longer current.

The registry persists one artifact per target so independent thunderstorm /
hail / cloudburst models can coexist without one overwriting another.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Mapping

from .model import (
    TrainableNowcastModel,
    default_model_store_path,
    STATUS_UNTRAINED,
    STATUS_TRAINED,
    STATUS_FAILED,
    STATUS_STALE,
    MODEL_FORMAT_VERSION,
)
from .manager import load_trained_model

logger = logging.getLogger(__name__)

DEFAULT_TARGETS: tuple[str, ...] = ("thunderstorm", "hail", "cloudburst")


def target_model_path(models_dir: Path, target: str, default_name: str = "thundercast_model") -> Path:
    """Return the artifact path for a given target."""
    return models_dir / f"{default_name}_{target}.json"


def discover_registry(models_dir: Path | None = None) -> dict[str, dict]:
    """Return honest status for each target artifact found on disk.

    Returns a mapping target -> status descriptor containing at least
    ``status`` and ``model_version`` (or nothing if the artifact is absent).
    """
    models_dir = models_dir or default_model_store_path().parent
    entries: dict[str, dict] = {}
    if not models_dir.exists():
        return {}
    for pattern_name in ("thundercast_model_*", "thundercast_model"):
        for path in models_dir.glob(f"{pattern_name}.json"):
            target = _target_from_filename(path.stem)
            if target is None:
                continue
            model = load_trained_model(path)
            if model is None:
                # Artifact exists but is not a valid trained model.
                entries[target] = {"status": _file_status(path), "artifact_path": str(path), "model_version": None}
            else:
                entries[target] = {
                    "status": model.metadata.status,
                    "model_version": model.metadata.model_version,
                    "target": model.metadata.target,
                    "dataset_name": model.metadata.dataset_name,
                    "dataset_version": model.metadata.dataset_version,
                    "trained_at": model.metadata.trained_at,
                    "n_train": model.metadata.n_train,
                    "n_validation": model.metadata.n_validation,
                    "n_test": model.metadata.n_test,
                    "metrics": model.metadata.metrics,
                    "artifact_path": str(path),
                }
    return entries


def registry_status(targets: tuple[str, ...] = DEFAULT_TARGETS) -> dict:
    """Return a human/API-friendly registry summary.

    Always marks targets as UNTRAINED when no genuine artifact exists (the
    honest default), returning the full set of supported targets.
    """
    entries = discover_registry()
    result: dict[str, dict] = {}
    any_trained = False
    for target in targets:
        entry = entries.get(target)
        if entry is not None:
            result[target] = entry
            if entry.get("status") == STATUS_TRAINED:
                any_trained = True
        else:
            result[target] = {"status": STATUS_UNTRAINED, "model_version": None, "target": target}
    return {"targets": list(targets), "any_trained": any_trained, "artifacts": result}


def _target_from_filename(stem: str) -> str | None:
    # "thundercast_model_thunderstorm" -> "thunderstorm"; "thundercast_model" is the legacy default.
    if stem == "thundercast_model":
        return "thunderstorm"
    prefix = "thundercast_model_"
    if stem.startswith(prefix):
        target = stem[len(prefix):]
        return target if target in DEFAULT_TARGETS else None
    return None


def _file_status(path: Path) -> str:
    """Classify an existing-but-invalid/untrained artifact file."""
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        meta = payload.get("metadata", {})
        saved = meta.get("status")
        if saved == STATUS_TRAINED:
            return STATUS_STALE  # tagged trained but failed our validation -> stale
        if saved in (STATUS_FAILED, STATUS_STALE):
            return saved
        return STATUS_UNTRAINED
    except Exception:  # noqa: BLE001 - malformed file
        return STATUS_FAILED


def mark_status(model: TrainableNowcastModel, status: str) -> TrainableNowcastModel:
    """Override a model's persisted status (used for FAILED/STALE handling)."""
    if status not in (STATUS_UNTRAINED, STATUS_TRAINED, STATUS_FAILED, STATUS_STALE):
        raise ValueError(f"invalid model status: {status}")
    model.metadata.status = status
    return model
