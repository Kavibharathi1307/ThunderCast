"""Base helpers for converting between MongoDB documents and schemas."""

from datetime import datetime, timezone


def isoformat_utc(dt: datetime | None) -> str | None:
    """Return a UTC ISO-8601 string for a datetime (or None)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()
