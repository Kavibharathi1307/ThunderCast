"""Explainability service.

Builds human-readable and structured explanations for every prediction so the
frontend can answer "Why is this location at risk?".

Each explanation includes:
* a natural-language summary
* top contributing factors (positive risk drivers)
* reducing factors (negative / absent drivers that lower risk)
* the model/baseline version and label

Honesty: drivers are derived from the *baseline* rules engine, not from a
trained model. Nothing here claims statistical validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .features import ModelFeatures
from .predictor import NowcastResult
from .risk_engine import StructuredRisk
from .thresholds import BASELINE_MODEL_LABEL, BASELINE_MODEL_VERSION

# Higher contribution -> considered a positive risk driver.
POSITIVE_DRIVER_MIN = 0.08
# Factors whose absence is notable (contribution falls in this band -> reducing).
NEGATIVE_DRIVER_MAX = 0.02

FACTOR_EXPLANATIONS: dict[str, str] = {
    "Humidity": "Elevated low-level moisture fuels convective development.",
    "Temperature": "Strong surface heating increases atmospheric instability.",
    "Pressure": "Falling/low pressure signals an unstable, storm-favourable environment.",
    "CAPE": "High convective available potential energy indicates strong updrafts.",
    "Lifted Index": "A deeply unstable lifted index supports rapid vertical motion.",
    "Wind Shear": "Vertical wind shear organises storms and sustains them.",
    "Precipitation": "Ongoing precipitation indicates active convection overhead.",
}


@dataclass
class DriverExplanation:
    """One factor in an explanation."""

    factor: str
    role: str  # "POSITIVE" | "REDUCING"
    impact: str
    contribution: float
    description: str


@dataclass
class PredictionExplanation:
    """Complete explanation of a prediction."""

    prediction_type: str  # e.g. "thunderstorm" | "overall_risk"
    risk_level: str
    summary: str
    drivers: list[DriverExplanation]
    positive_drivers: list[str]
    reducing_factors: list[str]
    confidence: float
    model_label: str = BASELINE_MODEL_LABEL
    model_version: str = BASELINE_MODEL_VERSION


def explain_structured_risk(risk: StructuredRisk) -> PredictionExplanation:
    """Explain a structured risk assessment."""
    if not risk.drivers:
        summary = (
            f"{risk.risk_level} convective risk estimated from limited "
            f"available signals with {risk.confidence:.0%} confidence."
        )
        return PredictionExplanation(
            prediction_type="overall_risk",
            risk_level=risk.risk_level,
            summary=summary,
            drivers=[],
            positive_drivers=[],
            reducing_factors=[],
            confidence=risk.confidence,
        )

    positive = [
        d for d in risk.drivers if d.contribution >= POSITIVE_DRIVER_MIN
    ]
    reducing = [
        d.factor
        for d in risk.drivers
        if d.contribution <= NEGATIVE_DRIVER_MAX
    ]

    driver_explanations = [
        DriverExplanation(
            factor=d.factor,
            role="POSITIVE" if d.contribution >= POSITIVE_DRIVER_MIN else "REDUCING",
            impact=d.impact,
            contribution=d.contribution,
            description=FACTOR_EXPLANATIONS.get(
                d.factor,
                f"{d.factor} contributes to the convective risk assessment.",
            ),
        )
        for d in risk.drivers
    ]

    top = positive[:3]
    if top:
        reasons = " ".join(f"{d.factor} ({d.impact.lower()})" for d in top)
        summary = (
            f"{risk.risk_level} convective risk ({risk.confidence:.0%} confidence). "
            f"Why? {reasons}. Overall risk score {risk.risk_score:.2f}."
        )
    else:
        summary = (
            f"{risk.risk_level} convective risk with {risk.confidence:.0%} "
            f"confidence and no dominant positive driver."
        )

    return PredictionExplanation(
        prediction_type="overall_risk",
        risk_level=risk.risk_level,
        summary=summary,
        drivers=driver_explanations,
        positive_drivers=[d.factor for d in positive],
        reducing_factors=reducing,
        confidence=risk.confidence,
    )


def explain_nowcast(nowcast: NowcastResult) -> PredictionExplanation:
    """Explain a full 0-6h nowcast using its peak risk and the top point."""
    peak_point = max(
        nowcast.points,
        key=lambda p: max(
            p.thunderstorm_probability, p.hail_probability, p.cloudburst_probability
        ),
        default=None,
    )
    if peak_point is None:
        return PredictionExplanation(
            prediction_type="nowcast",
            risk_level=nowcast.peak_risk,
            summary="No nowcast points were generated.",
            drivers=[],
            positive_drivers=[],
            reducing_factors=[],
            confidence=0.0,
        )

    peak_val = max(
        peak_point.thunderstorm_probability,
        peak_point.hail_probability,
        peak_point.cloudburst_probability,
    )
    driving_hazard = (
        "thunderstorm"
        if peak_point.thunderstorm_probability >= peak_val
        else "hail"
        if peak_point.hail_probability >= peak_val
        else "cloudburst"
    )

    reasons: list[str] = []
    if peak_point.thunderstorm_probability >= 0.5:
        reasons.append("high thunderstorm probability (>50%)")
    if peak_point.hail_probability >= 0.4:
        reasons.append("elevated hail probability")
    if peak_point.cloudburst_probability >= 0.5:
        reasons.append("elevated cloudburst/heavy-rain probability")

    if not reasons:
        reasons.append("moderate to low convective signals")

    window = (
        f"Risk peaks in the {nowcast.peak_hour}-hour horizon"
        if nowcast.peak_hour is not None
        else "Risk timing uncertain"
    )
    summary = (
        f"{nowcast.peak_risk} {driving_hazard} risk at this location. "
        f"Why? {' , '.join(reasons)}. {window} with "
        f"{peak_point.confidence:.0%} confidence."
    )

    driver_explanations = [
        DriverExplanation(
            factor="Thunderstorm",
            role="POSITIVE" if peak_point.thunderstorm_probability >= 0.5 else "REDUCING",
            impact="HIGH" if peak_point.thunderstorm_probability >= 0.6 else "MODERATE",
            contribution=peak_point.thunderstorm_probability,
            description="Probabilistic thunderstorm nowcast for this window.",
        ),
        DriverExplanation(
            factor="Hail",
            role="POSITIVE" if peak_point.hail_probability >= 0.4 else "REDUCING",
            impact="HIGH" if peak_point.hail_probability >= 0.5 else "MODERATE",
            contribution=peak_point.hail_probability,
            description="Probabilistic hail nowcast for this window.",
        ),
        DriverExplanation(
            factor="Cloudburst",
            role="POSITIVE" if peak_point.cloudburst_probability >= 0.4 else "REDUCING",
            impact="HIGH" if peak_point.cloudburst_probability >= 0.5 else "MODERATE",
            contribution=peak_point.cloudburst_probability,
            description="Probabilistic cloudburst/heavy-rain nowcast for this window.",
        ),
    ]
    positive_drivers = [d.factor for d in driver_explanations if d.role == "POSITIVE"]
    reducing = [d.factor for d in driver_explanations if d.role == "REDUCING"]

    return PredictionExplanation(
        prediction_type="nowcast",
        risk_level=nowcast.peak_risk,
        summary=summary,
        drivers=driver_explanations,
        positive_drivers=positive_drivers,
        reducing_factors=reducing,
        confidence=peak_point.confidence,
    )
