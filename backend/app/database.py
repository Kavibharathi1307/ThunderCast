"""MongoDB connection management using PyMongo.

This module is responsible for creating and reusing a single MongoDB client
and exposing collection access. It is designed to be resilient: the backend
must start and serve endpoints even when MongoDB Atlas is unavailable.
"""

from __future__ import annotations

import logging

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure, ServerSelectionTimeoutError

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_settings: Settings | None = None


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
