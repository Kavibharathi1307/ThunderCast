"""Shared pytest fixtures.

MongoDB is never required for tests -- the default state has no MONGO_URI
configured, and we patch the health service to simulate connected /
unavailable states without a live Atlas connection.
"""

import pytest


@pytest.fixture(autouse=True)
def _clear_mongo_state(monkeypatch):
    """Force a clean per-test Mongo state and block real connections."""
    import app.database as database

    database._client = None
    database._settings = None
    monkeypatch.delenv("MONGO_URI", raising=False)
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    yield
    database.close_connection()


@pytest.fixture
def mongo_connected(monkeypatch):
    """Simulate MongoDB being reachable by stubbing the health route."""
    import app.routes.health as health_route

    monkeypatch.setattr(health_route, "get_database_status", lambda: "connected")
    return health_route


@pytest.fixture
def mongo_unavailable(monkeypatch):
    """Simulate MongoDB being unreachable by stubbing the health route."""
    import app.routes.health as health_route

    monkeypatch.setattr(health_route, "get_database_status", lambda: "unavailable")
    return health_route
