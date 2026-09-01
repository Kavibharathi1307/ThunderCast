"""Demo API response tests.

These verify every data endpoint returns a valid, clearly-labelled demo
response -- and that responses remain available even with no Mongo configured.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_LAT = 28.6
VALID_LON = 77.2


def _assert_demo(body, field):
    assert body["demo"] is True
    assert "demo_note" in body
    assert field in body["data"] or field in body


def test_current_weather_demo():
    resp = client.get(f"/api/weather/current?latitude={VALID_LAT}&longitude={VALID_LON}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["data"]["latitude"] == VALID_LAT
    assert body["data"]["longitude"] == VALID_LON


def test_forecast_demo():
    resp = client.get(f"/api/forecast/{VALID_LAT}/{VALID_LON}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert len(body["points"]) == 7
    assert body["points"][0]["lead_time_hours"] == 0.0
    assert body["points"][-1]["lead_time_hours"] == 6.0


def test_risk_demo():
    resp = client.get(f"/api/risk/{VALID_LAT}/{VALID_LON}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["data"]["overall_risk"] in {"LOW", "MODERATE", "HIGH", "EXTREME"}


def test_alerts_demo():
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["count"] == len(body["alerts"])


def test_historical_demo():
    resp = client.get("/api/historical")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["count"] == len(body["events"])


def test_risk_grid_demo():
    resp = client.get("/api/map/risk-grid")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert len(body["data"]["cells"]) > 0
    assert "bounds" in body["data"]


def test_demo_responses_available_without_mongo(mongo_unavailable):
    for url in ("/api/alerts", "/api/historical", "/api/map/risk-grid"):
        resp = client.get(url)
        assert resp.status_code == 200, url
