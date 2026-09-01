"""Prototype 0-6 hour nowcasting engine.

Produces horizon-by-horizon probabilistic forecasts for thunderstorm, hail
and cloudburst/heavy-rain over the 0-6 hour window.

IMPORTANT (honesty)
-------------------
This is a **BASELINE / pseudo-ML** engine. It applies domain-inspired,
deterministic heuristics to the features supplied by a data provider. It is
NOT a trained, validated operational meteorological model and must not be
presented as one. Outputs are tagged with the baseline model label and version
so consumption layers can distinguish them from a future trained model.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .features import ModelFeatures
from .thresholds import BASELINE_THRESHOLDS, BASELINE_MODEL_LABEL, BASELINE_MODEL_VERSION, ConvectiveThresholds

HORIZONS_HOURS = [1, 2, 3, 4, 5, 6]  # 0-1, 1-2, ..., 5-6


@dataclass
class NowcastPoint:
    """A single nowcast for a location at a given forecast horizon."""

    latitude: float
    longitude: float
    forecast_time: datetime
    horizon_hours: int
    thunderstorm_probability: float
    hail_probability: float
    cloudburst_probability: float
    overall_risk: str
    confidence: float
    model_label: str = BASELINE_MODEL_LABEL
    model_version: str = BASELINE_MODEL_VERSION


@dataclass
class NowcastResult:
    """Full nowcast for a location across the 0-6 hour window."""

    latitude: float
    longitude: float
    forecast_time: datetime
    window_hours: int = 6
    points: list[NowcastPoint] = field(default_factory=list)
    peak_risk: str = "LOW"
    peak_hour: int | None = None
    risk_start_hour: int | None = None
    risk_end_hour: int | None = None
    model_label: str = BASELINE_MODEL_LABEL
    model_version: str = BASELINE_MODEL_VERSION


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _bump(x: float, alpha: float) -> float:
    return _clamp(x * alpha)


def _risk_level(peak: float, t: ConvectiveThresholds) -> str:
    if peak >= t.extreme_peak:
        return "EXTREME"
    if peak >= t.high_peak:
        return "HIGH"
    if peak >= t.moderate_peak:
        return "MODERATE"
    return "LOW"


def _base_probabilities(features: ModelFeatures, t: ConvectiveThresholds) -> dict:
    """Compute location baseline probabilities from features (0-1)."""
    obs = features.observation
    stab = features.stability
    rad = features.radar
    ltg = features.lightning

    # --- Thunderstorm ---
    ts = 0.10
    if obs.relative_humidity_percent is not None:
        ts += _clamp((obs.relative_humidity_percent - 50.0) / 50.0) * t.weight_humidity
    if obs.temperature_c is not None:
        ts += _clamp((obs.temperature_c - 25.0) / 15.0) * t.weight_temperature
    if obs.pressure_hpa is not None:
        ts += _clamp((1013.0 - obs.pressure_hpa) / 20.0) * t.weight_pressure
    if stab.cape_jkg is not None:
        ts += _clamp(stab.cape_jkg / 3000.0) * t.weight_cape
    if stab.lifted_index_c is not None:
        ts += _clamp((-stab.lifted_index_c - 2.0) / 8.0) * t.weight_lifted_index
    if stab.wind_shear_ms is not None:
        ts += _clamp(stab.wind_shear_ms / 30.0) * t.weight_shear
    if ltg.lightning_density_km2_hr is not None:
        ts += _clamp(ltg.lightning_density_km2_hr / 10.0) * t.weight_lightning
    thunderstorm = _clamp(ts)

    # --- Hail --- (needs strong instability + high reflectivity / echo tops)
    hail = thunderstorm * 0.40
    if rad.max_reflectivity_dbz is not None and rad.max_reflectivity_dbz >= t.high_reflectivity_dbz:
        hail += 0.20
    if rad.echo_top_km is not None and rad.echo_top_km >= t.high_echo_top_km:
        hail += 0.10
    if stab.cape_jkg is not None and stab.cape_jkg > t.high_cape_jkg:
        hail += 0.10
    hail = _clamp(hail)

    # --- Cloudburst / heavy rain --- (saturated + intense precipitation)
    cb = 0.05
    if obs.relative_humidity_percent is not None and obs.relative_humidity_percent > t.high_humidity_percent:
        cb += 0.15
    if obs.precipitation_rate_mmh is not None:
        cb += _clamp(obs.precipitation_rate_mmh / t.extreme_precipitation_mmh) * t.weight_precip_rate
    if obs.precipitation_mm is not None and obs.precipitation_mm > 10.0:
        cb += 0.10
    if stab.cape_jkg is not None and stab.cape_jkg > t.high_cape_jkg:
        cb += 0.05
    cloudburst = _clamp(cb)

    return {
        "thunderstorm": thunderstorm,
        "hail": hail,
        "cloudburst": cloudburst,
    }


def _confidence(features: ModelFeatures, t: ConvectiveThresholds) -> float:
    """Estimate confidence from how much feature data is available."""
    score = t.confidence_base
    for value in (
        features.observation.relative_humidity_percent,
        features.observation.temperature_c,
        features.stability.cape_jkg,
        features.stability.lifted_index_c,
        features.stability.wind_shear_ms,
        features.radar.max_reflectivity_dbz,
        features.radar.echo_top_km,
        features.lightning.lightning_density_km2_hr,
    ):
        if value is not None:
            score += t.confidence_feature_bonus
    return _clamp(score, 0.3, 0.95)


def _time_decay(base: float, horizon: int, weather_driven: bool) -> float:
    """Apply a simple evolution curve over the nowcast horizon.

    A weather-driven signal slowly relaxes back toward the long-term mean over
    the 0-6 hour window. This is a transparent baseline assumption, not a real
    temporal model.
    """
    if not weather_driven:
        return base
    # mild decay factor per hour; capped so probability stays plausible
    factor = math.exp(-horizon * 0.06)
    return _clamp(base * factor)


def generate_nowcast(
    features: ModelFeatures,
    thresholds: ConvectiveThresholds | None = None,
    forecast_time: datetime | None = None,
) -> NowcastResult:
    """Generate a 0-6 hour nowcast for a location from model features.

    The caller (service layer) is responsible for labelling the output as
    DEMO/BASELINE when fed demo features. This engine itself never claims to
    be a trained model.
    """
    t = thresholds or BASELINE_THRESHOLDS
    now = forecast_time or datetime.now(timezone.utc)
    base = _base_probabilities(features, t)
    confidence = _confidence(features, t)

    avg = (base["thunderstorm"] + base["hail"] + base["cloudburst"]) / 3.0

    points: list[NowcastPoint] = []
    for horizon in HORIZONS_HOURS:
        thunder = _time_decay(base["thunderstorm"], horizon, weather_driven=True)
        hail = _time_decay(base["hail"], horizon, weather_driven=True)
        cloudburst = _time_decay(base["cloudburst"], horizon, weather_driven=True)
        peak = max(thunder, hail, cloudburst)
        horizon_conf = _clamp(confidence * (1.0 - horizon * 0.03))
        points.append(
            NowcastPoint(
                latitude=features.latitude,
                longitude=features.longitude,
                forecast_time=_add_hours(now, horizon),
                horizon_hours=horizon,
                thunderstorm_probability=round(thunder, 4),
                hail_probability=round(hail, 4),
                cloudburst_probability=round(cloudburst, 4),
                overall_risk=_risk_level(peak, t),
                confidence=round(horizon_conf, 4),
            )
        )

    # Overall window risk / timing
    peak_point = max(points, key=lambda p: max(p.thunderstorm_probability, p.hail_probability, p.cloudburst_probability))
    peak_risk = peak_point.overall_risk

    # Risk time window: hours where peak >= MODERATE threshold
    affected = [p.horizon_hours for p in points if _risk_level(max(p.thunderstorm_probability, p.hail_probability, p.cloudburst_probability), t) in ("MODERATE", "HIGH", "EXTREME")]
    risk_start = min(affected) if affected else None
    risk_end = max(affected) if affected else None

    return NowcastResult(
        latitude=features.latitude,
        longitude=features.longitude,
        forecast_time=now,
        points=points,
        peak_risk=peak_risk,
        peak_hour=peak_point.horizon_hours,
        risk_start_hour=risk_start,
        risk_end_hour=risk_end,
    )


def _add_hours(dt: datetime, hours: int) -> datetime:
    from datetime import timedelta

    return dt + timedelta(hours=hours)
