"""Unit tests for the real (Open-Meteo) providers.

These tests **never** hit the network: ``urllib.request.urlopen`` is stubbed to
return a canned JSON payload, so the provider is exercised end-to-end offline.
"""

import json

import pytest

from app.ml.real_providers import (
    OpenMeteoWeatherProvider,
    RealWeatherProvider,
    ProviderUnavailable,
    REAL_PROVENANCE_LABEL,
    resolve_feature_provider,
)
from app.ml.providers import DemoDataProvider


CANONICAL_PAYLOAD = {
    "current": {
        "temperature_2m": 31.5,
        "relative_humidity_2m": 78.3,
        "dew_point_2m": 24.1,
        "surface_pressure": 1003.2,
        "wind_speed_10m": 6.2,
        "wind_direction_10m": 180.0,
        "wind_gusts_10m": 12.0,
        "precipitation": 0.2,
        "precipitation_rate": 1.1,
        "cloud_cover": 75.0,
        "cape": 1450.0,
        "cin": 20.0,
        "lifted_index": -2.5,
    }
}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _provider(monkeypatch, payload=CANONICAL_PAYLOAD):
    recorded = {}

    def fake_urlopen(url, timeout=0):
        recorded["url"] = url
        return _FakeResponse(payload)

    monkeypatch.setattr("app.ml.real_providers.urllib.request.urlopen", fake_urlopen)
    provider = OpenMeteoWeatherProvider(allowed=True)
    return provider, recorded


def test_observation_maps_real_fields(monkeypatch):
    provider, _ = _provider(monkeypatch)
    obs = provider.get_observation(19.0, 72.0)
    assert obs.temperature_c == pytest.approx(31.5)
    assert obs.relative_humidity_percent == pytest.approx(78.3)
    assert obs.pressure_hpa == pytest.approx(1003.2)
    assert obs.wind_speed_ms == pytest.approx(6.2)
    assert obs.precipitation_rate_mmh == pytest.approx(1.1)
    assert obs.cloud_cover_percent == pytest.approx(75.0)


def test_stability_maps_real_fields(monkeypatch):
    provider, _ = _provider(monkeypatch)
    stab = provider.get_stability(19.0, 72.0)
    assert stab.cape_jkg == pytest.approx(1450.0)
    assert stab.cin_jkg == pytest.approx(20.0)
    assert stab.lifted_index_c == pytest.approx(-2.5)
    assert stab.dewpoint_depression_c == pytest.approx(31.5 - 24.1)


def test_build_features_composite(monkeypatch):
    provider, _ = _provider(monkeypatch)
    composite = RealWeatherProvider(provider)
    mf = composite.build_features(19.0, 72.0)
    assert mf.observation.temperature_c == pytest.approx(31.5)
    # Radar/satellite/lightning remain empty (no bundled public source).
    assert mf.radar.max_reflectivity_dbz is None
    assert mf.satellite.cloud_top_temperature_k is None
    assert mf.lightning.lightning_density_km2_hr is None


def test_provenance_label_is_real(monkeypatch):
    provider, _ = _provider(monkeypatch)
    assert provider.provenance == REAL_PROVENANCE_LABEL


def test_disabled_provider_raises_unavailable():
    provider = OpenMeteoWeatherProvider(allowed=False)
    with pytest.raises(ProviderUnavailable):
        provider.get_observation(19.0, 72.0)


def test_provider_raises_on_network_error(monkeypatch):
    def boom(url, timeout=0):
        raise OSError("connection refused")

    monkeypatch.setattr("app.ml.real_providers.urllib.request.urlopen", boom)
    provider = OpenMeteoWeatherProvider(allowed=True)
    with pytest.raises(ProviderUnavailable):
        provider.get_observation(19.0, 72.0)


def test_resolve_provider_defaults_to_demo():
    provider = resolve_feature_provider(allowed=False)
    assert isinstance(provider, DemoDataProvider)
