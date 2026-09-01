"""Service for database connectivity / health reporting.

The health endpoint must *never* block waiting for MongoDB.  It reads a
cached status that is kept fresh by a background daemon thread in
``database.py``.
"""

from __future__ import annotations

from ..database import get_database_status as _cached_db_status


def get_database_status() -> str:
    """Return ``"connected"`` or ``"unavailable"`` from the background cache."""
    return _cached_db_status()
