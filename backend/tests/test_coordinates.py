"""Coordinate validation tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("lat,lon", [(28.0, 77.0), (-90.0, -180.0), (90.0, 180.0), (0.0, 0.0)])
def test_valid_coordinates_accepted(lat, lon):
    resp = client.get(f"/api/risk/{lat}/{lon}")
    assert resp.status_code == 200


@pytest.mark.parametrize("lat", [91.0, -91.0, 100.0, -200.0])
def test_invalid_latitude_rejected(lat):
    resp = client.get(f"/api/risk/{lat}/77.0")
    assert resp.status_code == 422


@pytest.mark.parametrize("lon", [181.0, -181.0, 300.0, -500.0])
def test_invalid_longitude_rejected(lon):
    resp = client.get(f"/api/risk/28.0/{lon}")
    assert resp.status_code == 422


@pytest.mark.parametrize("bad", ["abc", "1,2"])
def test_non_numeric_coordinates_rejected(bad):
    resp = client.get(f"/api/forecast/{bad}/77.0")
    assert resp.status_code == 422


def test_empty_coordinate_path_segment_not_found():
    # An empty path segment does not match the route -> 404, not a crash.
    resp = client.get("/api/forecast//77.0")
    assert resp.status_code == 404
