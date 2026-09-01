"""API-level tests for environment_mode / data provenance wiring.

Verifies that the endpoints now surface the honest DEMO-mode metadata in their
payloads. (REAL mode requires an outbound provider and is covered at the unit
level; here we assert the DEMO default is explicit and consistent.)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID = (21.25, 78.5)


def test_nowcast_exposes_environment_mode():
    body = client.get("/api/nowcast", params={"latitude": VALID[0], "longitude": VALID[1]}).json()
    assert body["environment_mode"] == "DEMO"
    assert body["data_provenance"] == "DEMO DATA"


def test_forecast_exposes_environment_mode():
    body = client.get(f"/api/forecast/{VALID[0]}/{VALID[1]}").json()
    assert body["environment_mode"] == "DEMO"
    assert body["data_provenance"] == "DEMO DATA"


def test_risk_exposes_environment_mode():
    body = client.get(f"/api/risk/{VALID[0]}/{VALID[1]}").json()
    assert body["environment_mode"] == "DEMO"
    assert body["data_provenance"] == "DEMO DATA"


def test_analytics_exposes_environment_mode_and_honest_status():
    body = client.get("/api/analytics/model").json()
    assert body["environment_mode"] == "DEMO"
    assert body["model_status"] == "UNTRAINED"
    assert body["data_provenance"] == "DEMO DATA"
