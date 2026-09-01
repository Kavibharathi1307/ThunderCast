"""Loader that discovers a previously-trained model from the model store.

The app keeps running on the BASELINE engine unless a genuinely-trained model
file exists. This module centralises that decision so services can safely ask
"is there a trained model available?" without knowing where files live.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .model import TrainableNowcastModel, default_model_store_path

logger = logging.getLogger(__name__)


def load_trained_model(store_path: str | Path | None = None) -> TrainableNowcastModel | None:
    """Return the persisted trained model, or ``None`` if unavailable/invalid.

    Never raises: a missing or malformed store simply yields ``None`` so the
    caller keeps using the BASELINE engine.
    """
    path = Path(store_path) if store_path else default_model_store_path()
    if not path.exists():
        return None
    try:
        model = TrainableNowcastModel.load(path)
        if model.is_trained:
            return model
        logger.info("Model store exists but is UNTRAINED: %s", path)
        return None
    except Exception as exc:  # pragma: no cover - defensive load
        logger.warning("Failed to load trained model from %s: %s", path, exc)
        return None
