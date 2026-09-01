"""Tests for MongoDB-unavailable behaviour.

These verify the application stays responsive and reports an accurate
database status when MongoDB is not configured or unreachable -- no real
Atlas connection is required.
"""

from fastapi.testclient import TestClient

from app.main import app
import app.database as database

client = TestClient(app)


def test_database_ping_returns_false_when_no_uri(_clear_mongo_state):
    assert database.get_client() is None
    assert database.ping_database() is False


def test_get_collection_returns_none_when_unavailable(_clear_mongo_state):
    assert database.get_collection("alerts") is None


def test_health_still_serves_when_database_unavailable(_clear_mongo_state):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["database"] == "unavailable"


def test_data_routes_still_serve_when_database_unavailable(_clear_mongo_state):
    for url in ("/api/alerts", "/api/historical", "/api/map/risk-grid"):
        assert client.get(url).status_code == 200, url
    assert client.get("/api/risk/28.0/77.0").status_code == 200


def test_close_connection_resets_state(_clear_mongo_state):
    database.close_connection()
    assert database._client is None
