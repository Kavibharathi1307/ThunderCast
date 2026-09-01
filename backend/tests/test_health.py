"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["service"] == "ThunderCast AI"
    assert body["database"] in {"connected", "unavailable"}


def test_health_database_unavailable_when_no_mongo(mongo_unavailable):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["database"] == "unavailable"


def test_health_database_connected_when_mongo_reachable(mongo_connected):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["database"] == "connected"


def test_health_response_has_expected_keys():
    resp = client.get("/api/health")
    body = resp.json()
    assert {"status", "service", "database"} <= set(body.keys())
