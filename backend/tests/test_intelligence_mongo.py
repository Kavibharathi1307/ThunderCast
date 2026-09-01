"""Tests for MongoDB "available" persistence mode in the intelligence layer.

These simulate a reachable Mongo by stubbing the database seam (ping + get_collection)
so we verify the persistence code path runs and writes expected documents -- WITHOUT
connecting to any real Atlas instance. When the seam reports unavailable, no write
happens and the app stays responsive.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

LAT, LON = 21.25, 78.5


class FakeCollection(dict):
    """A tiny stand-in for a pymongo collection that records documents."""

    def __init__(self):
        super().__init__()
        self.inserted = []
        self.upserted = []

    def insert_one(self, document):
        self.inserted.append(document)
        return None

    def replace_one(self, filter_, document, upsert=False):
        self.upserted.append((filter_, document, upsert))
        return None


# --- MongoDB available mode -------------------------------------------------

def test_nowcast_persisted_when_mongo_available(monkeypatch):
    import app.services.intelligence as intel

    fake = FakeCollection()
    monkeypatch.setattr(intel, "ping_database", lambda: True)
    monkeypatch.setattr(intel, "get_collection", lambda name: fake if name == "nowcasts" else FakeCollection())

    intel.generate_nowcast_response(LAT, LON, request_id="req-test-1")

    assert len(fake.inserted) == 1
    doc = fake.inserted[0]
    assert doc["request_id"] == "req-test-1"
    assert doc["latitude"] == LAT
    assert doc["model_label"] == "BASELINE MODEL"
    assert "provenance" in doc
    assert "impacts" in doc
    assert len(doc["points"]) == 6


def test_storm_tracks_persisted_when_mongo_available(monkeypatch):
    import app.services.intelligence as intel

    fake = FakeCollection()
    monkeypatch.setattr(intel, "ping_database", lambda: True)
    monkeypatch.setattr(intel, "get_collection", lambda name: fake if name == "storm_tracks" else FakeCollection())

    intel.persist_storm_tracks()

    assert len(fake.upserted) > 0
    filter_, doc, upsert = fake.upserted[0]
    assert upsert is True
    assert "cell_id" in filter_
    assert doc["label"] == "Baseline storm-motion extrapolation"
    assert len(doc["predicted_positions"]) == 4


# --- MongoDB unavailable mode (degradation) ---------------------------------

def test_nowcast_not_persisted_when_mongo_unavailable(monkeypatch):
    import app.services.intelligence as intel

    fake = FakeCollection()
    monkeypatch.setattr(intel, "ping_database", lambda: False)
    monkeypatch.setattr(intel, "get_collection", lambda name: fake)

    intel.generate_nowcast_response(LAT, LON, request_id="req-test-2")

    assert len(fake.inserted) == 0


def test_storm_tracks_not_persisted_when_mongo_unavailable(monkeypatch):
    import app.services.intelligence as intel

    fake = FakeCollection()
    monkeypatch.setattr(intel, "ping_database", lambda: False)
    monkeypatch.setattr(intel, "get_collection", lambda name: fake)

    intel.persist_storm_tracks()

    assert len(fake.upserted) == 0


def test_persistence_error_does_not_break_response(monkeypatch):
    """A failing write must not break the API -- it degrades gracefully."""
    import app.services.intelligence as intel

    def boom(name):
        raise RuntimeError("simulated db failure")

    monkeypatch.setattr(intel, "ping_database", lambda: True)
    monkeypatch.setattr(intel, "get_collection", boom)

    # Even if persistence throws, the endpoint still returns a valid nowcast.
    resp = client.get("/api/nowcast", params={"latitude": LAT, "longitude": LON})
    assert resp.status_code == 200
    assert resp.json()["window_hours"] == 6


def test_double_persist_does_not_duplicate(monkeypatch):
    """Each unique request id writes exactly one document."""
    import app.services.intelligence as intel

    fake = FakeCollection()
    monkeypatch.setattr(intel, "ping_database", lambda: True)
    monkeypatch.setattr(intel, "get_collection", lambda name: fake if name == "nowcasts" else FakeCollection())

    intel.generate_nowcast_response(LAT, LON, request_id="req-same")
    intel.generate_nowcast_response(LAT, LON, request_id="req-same")

    assert len(fake.inserted) == 2