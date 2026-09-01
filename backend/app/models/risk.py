"""Persistence models for risk assessments (``risk_assessments`` collection)."""

from ..schemas.risk import RiskAssessment
from .base import isoformat_utc


class RiskAssessmentModel:
    """Helpers for the ``risk_assessments`` collection."""

    @staticmethod
    def to_document(risk: RiskAssessment) -> dict:
        return {
            "latitude": risk.latitude,
            "longitude": risk.longitude,
            "timestamp": isoformat_utc(risk.timestamp),
            "thunderstorm_probability": risk.thunderstorm_probability,
            "hail_probability": risk.hail_probability,
            "cloudburst_probability": risk.cloudburst_probability,
            "overall_risk": risk.overall_risk,
            "confidence": risk.confidence,
            "explanation": risk.explanation,
        }
