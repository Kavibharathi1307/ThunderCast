"""Service for database connectivity / health reporting."""

from __future__ import annotations

from ..database import get_settings, ping_database


def get_database_status() -> str:
    """Return ``"connected"`` or ``"unavailable"`` based on a live ping."""
    settings = get_settings()
    if not settings.MONGO_URI:
        return "unavailable"
    return "connected" if ping_database() else "unavailable"
