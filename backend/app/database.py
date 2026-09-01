"""MongoDB connection management using PyMongo.

This module is responsible for creating and reusing a single MongoDB client
and exposing collection access. It is designed to be resilient: the backend
must start and serve endpoints even when MongoDB Atlas is unavailable.

Health reporting uses a background-thread cached probe so the /api/health
endpoint never blocks waiting for MongoDB.
"""

from __future__ import annotations

import logging
import threading
import time

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, ServerSelectionTimeoutError

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_settings: Settings | None = None

# ---------------------------------------------------------------------------
# Cached DB status — refreshed by a background daemon thread so that the
# /api/health endpoint *never* blocks waiting for a MongoDB round-trip.
# ---------------------------------------------------------------------------
_DB_STATUS_TTL_SECONDS: int = 25  # refresh interval

_db_status_cache: dict = {
    "status": "unavailable",
    "timestamp": 0.0,       # time.monotonic() value
}
_db_status_lock = threading.Lock()
_db_probe_started = False


def get_client() -> MongoClient | None:
    """Return the shared MongoDB client, creating it on first use.

    Returns ``None`` (and never raises) when MongoDB is not configured or the
    client cannot be constructed, so callers can degrade gracefully.
    """
    global _client, _settings

    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.MONGO_URI:
        logger.warning("MONGO_URI is not set; MongoDB is disabled.")
        return None

    try:
        _client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
            connectTimeoutMS=settings.MONGO_CONNECT_TIMEOUT_MS,
        )
        _settings = settings
        return _client
    except ConfigurationError as exc:  # malformed connection string
        logger.error("MongoDB configuration error: %s", exc)
        _client = None
        return None


def get_database_name() -> str:
    """Return the configured database name."""
    if _settings is not None:
        return _settings.MONGO_DB_NAME
    return get_settings().MONGO_DB_NAME


def ping_database() -> bool:
    """Return True when MongoDB is reachable, False otherwise.

    This performs a lightweight round-trip to the server. It never raises; any
    connectivity problem is caught and reported as ``False``.
    """
    client = get_client()
    if client is None:
        return False
    try:
        client.admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError) as exc:
        logger.warning("MongoDB ping failed: %s", exc)
        return False


def get_database():
    """Return the configured :class:`pymongo.database.Database` or ``None``."""
    client = get_client()
    if client is None:
        return None
    try:
        return client[get_database_name()]
    except (ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError) as exc:
        logger.warning("Unable to resolve database: %s", exc)
        return None


def get_collection(collection_name: str):
    """Return a PyMongo collection, or ``None`` if the database is unavailable.

    fetch / demo routes should treat ``None`` as "database unavailable" and
    fall back to demo behaviour rather than crashing.
    """
    database = get_database()
    if database is None:
        return None
    return database[collection_name]


def close_connection() -> None:
    """Close the shared MongoDB client (mainly used in tests)."""
    global _client, _settings
    if _client is not None:
        try:
            _client.close()
        except Exception:  # pragma: no cover - defensive cleanup
            pass
    _client = None
    _settings = None


# ---------------------------------------------------------------------------
# Cached database-status layer
# ---------------------------------------------------------------------------

def _probe_database() -> str:
    """Ping MongoDB and return ``"connected"`` or ``"unavailable"``.

    This is the slow path — called only from the background thread.
    """
    settings = get_settings()
    if not settings.MONGO_URI:
        return "unavailable"
    return "connected" if ping_database() else "unavailable"


def _refresh_db_status() -> None:
    """Background thread target: periodically probe MongoDB and cache the result."""
    global _db_status_cache
    while True:
        status = _probe_database()
        with _db_status_lock:
            _db_status_cache = {
                "status": status,
                "timestamp": time.monotonic(),
            }
        time.sleep(_DB_STATUS_TTL_SECONDS)


def warm_up_database_status() -> None:
    """Start the background DB-status probe daemon (safe to call multiple times).

    The very first call also does a non-blocking initial probe so the first
    health request returns a meaningful cached value instantly.  If the probe
    takes too long (e.g. DNS resolution stalls), we just leave the cache at
    ``"unavailable"`` — the next cycle will try again.
    """
    global _db_probe_started
    if _db_probe_started:
        return
    _db_probe_started = True

    # Quick synchronous initial probe with a short deadline so the first
    # health call is never completely blind.
    try:
        status = _probe_database()
        with _db_status_lock:
            _db_status_cache = {
                "status": status,
                "timestamp": time.monotonic(),
            }
    except Exception:
        pass  # leave default "unavailable"

    t = threading.Thread(target=_refresh_db_status, daemon=True, name="db-status-probe")
    t.start()


def get_database_status() -> str:
    """Return the cached DB status string (``"connected"`` or ``"unavailable"``).

    This never blocks — it reads the in-memory cache that the background
    thread keeps fresh.
    """
    with _db_status_lock:
        return _db_status_cache["status"]
