"""API-level tests for the intelligence endpoints (nowcast / impact / storms /
explainability / analytics)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID = (21.25, 78.5)


def test_nowcast_endpoint_structure():
    resp = client.get("/api/nowcast", params={"latitude": VALID[0], "longitude": VALID[1]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["window_hours"] == 6
    assert len(body["points"]) == 6
    assert body["model_label"] == "BASELINE MODEL"
    for p in body["points"]:
        assert 1 <= p["horizon_hours"] <= 6
        assert 0.0 <= p["thunderstorm_probability"] <= 1.0
        assert 0.0 <= p["hail_probability"] <= 1.0
        assert 0.0 <= p["cloudburst_probability"] <= 1.0
        assert 0.0 <= p["confidence"] <= 1.0
        assert p["overall_risk"] in {"LOW", "MODERATE", "HIGH", "EXTREME"}


def test_nowcast_path_params_matches_query():
    query = client.get("/api/nowcast", params={"latitude": VALID[0], "longitude": VALID[1]}).json()
    path = client.get(f"/api/nowcast/{VALID[0]}/{VALID[1]}").json()
    # Compare deterministic forecast fields (forecast_time differs as it is "now").
    strip = lambda pts: [
        {k: v for k, v in p.items() if k != "forecast_time"} for p in pts
    ]
    assert strip(query["points"]) == strip(path["points"])
    assert query["peak_risk"] == path["peak_risk"]


def test_forecast_timeline_alias():
    resp = client.get("/api/forecast/timeline", params={"latitude": VALID[0], "longitude": VALID[1]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["window_hours"] == 6
    assert len(body["points"]) == 6


def test_impact_endpoint():
    resp = client.get("/api/impact", params={"latitude": VALID[0], "longitude": VALID[1]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "PROTOTYPE IMPACT MODEL"
    assert "flooding" in body["impacts"]
    assert "roads" in body["impacts"]
    assert "agriculture" in body["impacts"]
    assert "lightning" in body["impacts"]
    assert "hail" in body["impacts"]
    assert "visibility" in body["impacts"]
    assert all(0.0 <= v <= 1.0 for v in body["impacts"].values())


def test_storm_predictions_endpoint():
    resp = client.get("/api/storms/predictions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["count"] == len(body["predictions"])
    assert len(body["predictions"]) > 0
    first = body["predictions"][0]
    assert first["label"] == "Baseline storm-motion extrapolation"
    assert [p["minutes_ahead"] for p in first["predicted_positions"]] == [30, 60, 90, 120]
    for pos in first["predicted_positions"]:
        assert 0.0 <= pos["intensity"] <= 1.0


def test_explainability_endpoint():
    resp = client.get("/api/explainability", params={"latitude": VALID[0], "longitude": VALID[1]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction_type"] == "overall_risk"
    assert body["summary"]
    assert body["model_label"] == "BASELINE MODEL"
    assert body["risk_level"] in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert isinstance(body["drivers"], list)


def test_explainability_nowcast_endpoint():
    resp = client.get("/api/explainability/nowcast", params={"latitude": VALID[0], "longitude": VALID[1]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction_type"] == "nowcast"
    assert body["summary"]
    assert len(body["drivers"]) >= 1


def test_model_analytics_endpoint_honest():
    resp = client.get("/api/analytics/model")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_label"] == "BASELINE MODEL"
    assert body["architecture"]
    # Honesty: evaluation status must be dataset_required (no real dataset)
    assert body["evaluation"]["status"] == "dataset_required"
    assert body["evaluation"]["n_samples"] == 0


def test_nowcast_invalid_latitude_rejected():
    resp = client.get("/api/nowcast", params={"latitude": 95.0, "longitude": 78.5})
    assert resp.status_code == 422


def test_nowcast_invalid_longitude_rejected():
    resp = client.get("/api/nowcast", params={"latitude": 21.0, "longitude": 200.0})
    assert resp.status_code == 422


def test_nowcast_missing_params_rejected():
    resp = client.get("/api/nowcast")
    assert resp.status_code == 422


def test_impact_invalid_params_rejected():
    resp = client.get("/api/impact", params={"latitude": "abc", "longitude": 78.0})
    assert resp.status_code == 422


def test_explainability_validates_coordinates():
    assert client.get("/api/explainability", params={"latitude": 22.0, "longitude": 190.0}).status_code == 422
    assert client.get("/api/explainability", params={"latitude": 92.0, "longitude": 70.0}).status_code == 422