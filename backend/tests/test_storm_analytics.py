"""Tests for storm tracking and analytics endpoints and the risk engine."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_storm_cells_demo():
    resp = client.get("/api/storm/cells")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["count"] == len(body["cells"])
    assert len(body["cells"]) > 0
    first = body["cells"][0]
    assert "id" in first
    assert "latitude" in first
    assert "longitude" in first
    assert "intensity" in first
    assert first["severity"] in {"LOW", "MODERATE", "HIGH", "EXTREME"}


def test_storm_tracks_demo():
    resp = client.get("/api/storm/tracks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["count"] == len(body["tracks"])
    assert len(body["tracks"]) > 0
    first = body["tracks"][0]
    assert "cell_id" in first
    assert "positions" in first
    assert "projected_positions" in first
    assert len(first["positions"]) > 0


def test_historical_analytics_demo():
    resp = client.get("/api/historical/analytics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    data = body["data"]
    assert "total_events" in data
    assert "event_types" in data
    assert "risk_distribution" in data
    assert "monthly_trends" in data
    assert data["total_events"] > 0


def test_risk_response_has_factors():
    resp = client.get("/api/risk/28.0/77.0")
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert "risk_factors" in data
    assert len(data["risk_factors"]) > 0
    first = data["risk_factors"][0]
    assert "name" in first
    assert "contribution" in first
    assert "description" in first
    assert "explanation" in data
    assert data["explanation"]
    assert data["confidence"] > 0


def test_alert_has_impacts():
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    body = resp.json()
    high_alerts = [a for a in body["alerts"] if a["severity"] == "HIGH"]
    assert high_alerts
    assert "impacts" in high_alerts[0]
    assert len(high_alerts[0]["impacts"]) > 0
    impact = high_alerts[0]["impacts"][0]
    assert "category" in impact
    assert "recommended_action" in impact


def test_risk_engine_outputs_bounded_probabilities():
    from app.ml.risk_engine import WeatherFeatures, assess_risk

    result = assess_risk(WeatherFeatures(latitude=20.0, longitude=78.0))
    assert 0.0 <= result.thunderstorm_probability <= 1.0
    assert 0.0 <= result.hail_probability <= 1.0
    assert 0.0 <= result.cloudburst_probability <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.overall_risk in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert result.explanation
    assert result.timestamp is not None


def test_humid_hot_conditions_increase_thunderstorm_risk():
    from app.ml.risk_engine import WeatherFeatures, assess_risk

    dry = assess_risk(
        WeatherFeatures(latitude=20.0, longitude=78.0, temperature_c=20, humidity_percent=40)
    )
    humid = assess_risk(
        WeatherFeatures(latitude=20.0, longitude=78.0, temperature_c=35, humidity_percent=90)
    )
    assert humid.thunderstorm_probability > dry.thunderstorm_probability
