"""Rule-based convective risk engine with explainable AI.

This module implements a deterministic risk assessment engine that combines
multiple meteorological indicators to produce probabilistic risk scores for
thunderstorms, hail, and cloudbursts. It is NOT a trained ML model -- it
applies domain-inspired heuristics to input features, producing explainable
outputs suitable for demonstration and development.

IMPORTANT: This engine has NOT been evaluated against real-world data.
Risk scores are illustrative and should NOT be used for operational forecasting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WeatherFeatures:
    """Input features for the risk engine."""

    latitude: float
    longitude: float
    temperature_c: float = 29.0
    humidity_percent: float = 70.0
    wind_speed_ms: float = 5.0
    wind_direction_deg: float = 180.0
    pressure_hpa: float = 1010.0
    precipitation_mm: float = 0.0
    cape_jkg: float | None = None
    lifted_index: float | None = None
    wind_shear_ms: float | None = None
    dewpoint_depression: float | None = None
    cloud_top_temp_k: float | None = None


@dataclass
class RiskFactor:
    """A single contributing factor to the risk assessment."""

    name: str
    contribution: float
    description: str


@dataclass
class RiskResult:
    """Complete risk assessment with explanations."""

    thunderstorm_probability: float
    hail_probability: float
    cloudburst_probability: float
    overall_risk: str
    confidence: float
    factors: list[RiskFactor] = field(default_factory=list)
    explanation: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _risk_level(peak: float) -> str:
    if peak >= 0.8:
        return "EXTREME"
    if peak >= 0.6:
        return "HIGH"
    if peak >= 0.4:
        return "MODERATE"
    return "LOW"


def _confidence_score(features: WeatherFeatures) -> float:
    """Estimate confidence based on data completeness and conditions."""
    score = 0.6
    if features.cape_jkg is not None:
        score += 0.1
    if features.lifted_index is not None:
        score += 0.1
    if features.wind_shear_ms is not None:
        score += 0.05
    if features.dewpoint_depression is not None:
        score += 0.05
    if features.cloud_top_temp_k is not None:
        score += 0.05
    return _clamp(score, 0.3, 0.95)


def assess_risk(features: WeatherFeatures) -> RiskResult:
    """Compute convective risk from meteorological features.

    This is a heuristic engine for demonstration purposes. The factors
    contributing to each hazard probability are tracked for explainability.
    """
    factors: list[RiskFactor] = []

    # --- Thunderstorm probability ---
    ts_base = 0.1

    # Humidity contribution (high moisture supports convection)
    hum_factor = _clamp((features.humidity_percent - 50) / 50) * 0.25
    factors.append(RiskFactor(
        name="Humidity",
        contribution=hum_factor,
        description=f"Humidity at {features.humidity_percent:.0f}% "
        f"({'elevated' if features.humidity_percent > 70 else 'moderate'} moisture)",
    ))
    ts_base += hum_factor

    # Temperature contribution (warm surface heating)
    temp_factor = _clamp((features.temperature_c - 25) / 15) * 0.2
    factors.append(RiskFactor(
        name="Temperature",
        contribution=temp_factor,
        description=f"Surface temperature {features.temperature_c:.1f}°C "
        f"({'strong' if features.temperature_c > 32 else 'moderate'} heating)",
    ))
    ts_base += temp_factor

    # Pressure tendency (falling pressure suggests instability)
    pres_factor = _clamp((1013 - features.pressure_hpa) / 20) * 0.15
    factors.append(RiskFactor(
        name="Pressure",
        contribution=pres_factor,
        description=f"Pressure {features.pressure_hpa:.0f} hPa "
        f"({'below normal' if features.pressure_hpa < 1008 else 'near normal'})",
    ))
    ts_base += pres_factor

    # CAPE contribution if available
    if features.cape_jkg is not None:
        cape_factor = _clamp(features.cape_jkg / 3000) * 0.2
        factors.append(RiskFactor(
            name="CAPE",
            contribution=cape_factor,
            description=f"CAPE {features.cape_jkg:.0f} J/kg "
            f"({'significant' if features.cape_jkg > 1500 else 'marginal'} instability)",
        ))
        ts_base += cape_factor

    # Lifted Index if available
    if features.lifted_index is not None:
        li_factor = _clamp((-features.lifted_index - 2) / 8) * 0.15
        factors.append(RiskFactor(
            name="Lifted Index",
            contribution=li_factor,
            description=f"Lifted Index {features.lifted_index:.1f} "
            f"({'unstable' if features.lifted_index < -3 else 'marginally unstable'})",
        ))
        ts_base += li_factor

    # Wind shear contribution
    if features.wind_shear_ms is not None:
        shear_factor = _clamp(features.wind_shear_ms / 30) * 0.1
        factors.append(RiskFactor(
            name="Wind Shear",
            contribution=shear_factor,
            description=f"Wind shear {features.wind_shear_ms:.0f} m/s "
            f"({'favorable' if features.wind_shear_ms > 15 else 'weak'} for organization)",
        ))
        ts_base += shear_factor

    # Current precipitation (feedback: ongoing convection)
    precip_factor = _clamp(features.precipitation_mm / 25) * 0.1
    if features.precipitation_mm > 0:
        factors.append(RiskFactor(
            name="Precipitation",
            contribution=precip_factor,
            description=f"Current rainfall {features.precipitation_mm:.1f} mm "
            f"(ongoing convective activity)",
        ))
        ts_base += precip_factor

    thunderstorm_prob = _clamp(ts_base)

    # --- Hail probability ---
    hail_base = thunderstorm_prob * 0.4
    if features.cape_jkg and features.cape_jkg > 2000:
        hail_base += 0.1
    if features.cloud_top_temp_k and features.cloud_top_temp_k < 200:
        hail_base += 0.08
    if features.wind_shear_ms and features.wind_shear_ms > 20:
        hail_base += 0.05
    hail_prob = _clamp(hail_base)

    # --- Cloudburst probability ---
    cloudburst_base = 0.05
    if features.humidity_percent > 75:
        cloudburst_base += 0.15
    if features.precipitation_mm > 10:
        cloudburst_base += 0.15
    if features.cape_jkg and features.cape_jkg > 1500:
        cloudburst_base += 0.1
    if features.temperature_c > 30 and features.humidity_percent > 80:
        cloudburst_base += 0.05
    cloudburst_prob = _clamp(cloudburst_base)

    # --- Overall risk ---
    peak = max(thunderstorm_prob, hail_prob, cloudburst_prob)
    overall = _risk_level(peak)
    confidence = _confidence_score(features)

    # --- Build explanation ---
    top_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)[:3]
    factor_summary = "; ".join(
        f"{f.name} (+{f.contribution:.0%})" for f in top_factors
    )
    explanation = (
        f"Risk assessment based on {len(factors)} meteorological indicators. "
        f"Primary contributors: {factor_summary}. "
        f"Overall {overall.lower()} risk ({thunderstorm_prob:.0%} thunderstorm, "
        f"{hail_prob:.0%} hail, {cloudburst_prob:.0%} cloudburst) with "
        f"{confidence:.0%} confidence."
    )

    return RiskResult(
        thunderstorm_probability=thunderstorm_prob,
        hail_probability=hail_prob,
        cloudburst_probability=cloudburst_prob,
        overall_risk=overall,
        confidence=confidence,
        factors=factors,
        explanation=explanation,
    )


# --- Structured / driver-based risk assessment (Phase 4) --------------------
#
# Extends the engine to return a machine-readable breakdown of *drivers*
# (factor, impact, contribution) in addition to the summary explanation.
# Backward compatible: `assess_risk()` above is unchanged.


@dataclass
class RiskDriver:
    """A single driver contributing to the overall risk."""

    factor: str
    impact: str  # HIGH / MODERATE / LOW
    contribution: float  # 0..1


@dataclass
class StructuredRisk:
    """Structured output of the risk engine for API / frontend consumption."""

    thunderstorm_probability: float
    hail_probability: float
    cloudburst_probability: float
    risk_level: str
    risk_score: float
    drivers: list[RiskDriver]
    explanation: str
    confidence: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _impact_label(contribution: float) -> str:
    if contribution >= 0.15:
        return "HIGH"
    if contribution >= 0.08:
        return "MODERATE"
    return "LOW"


def assess_risk_structured(features: WeatherFeatures) -> StructuredRisk:
    """Return a structured risk assessment with per-factor drivers.

    Reuses the same scientific weighting as :func:`assess_risk` but exposes a
    machine-readable drivers list (factor / impact / contribution) suitable for
    the explainability API and frontend.
    """
    result = assess_risk(features)

    drivers: list[RiskDriver] = []
    for factor in result.factors:
        drivers.append(
            RiskDriver(
                factor=factor.name,
                impact=_impact_label(factor.contribution),
                contribution=round(factor.contribution, 4),
            )
        )
    # Sort by contribution descending so positive drivers appear first.
    drivers.sort(key=lambda d: d.contribution, reverse=True)

    peak = max(result.thunderstorm_probability, result.hail_probability, result.cloudburst_probability)

    return StructuredRisk(
        thunderstorm_probability=result.thunderstorm_probability,
        hail_probability=result.hail_probability,
        cloudburst_probability=result.cloudburst_probability,
        risk_level=result.overall_risk,
        risk_score=round(peak, 4),
        drivers=drivers,
        explanation=result.explanation,
        confidence=result.confidence,
        timestamp=result.timestamp,
    )
