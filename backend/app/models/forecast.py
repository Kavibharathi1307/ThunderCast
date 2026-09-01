"""Persistence models for forecasts (``forecasts`` collection)."""

from datetime import datetime

from ..schemas.forecast import ForecastPoint
from .base import isoformat_utc


class ForecastModel:
    """Helpers for the ``forecasts`` collection."""

    @staticmethod
    def to_document(point: ForecastPoint) -> dict:
        return {
            "latitude": point.latitude,
            "longitude": point.longitude,
            "timestamp": isoformat_utc(point.timestamp),
            "lead_time_hours": point.lead_time_hours,
            "thunderstorm_probability": point.thunderstorm_probability,
            "hail_probability": point.hail_probability,
            "cloudburst_probability": point.cloudburst_probability,
            "precipitation_mm": point.precipitation_mm,
            "wind_speed_ms": point.wind_speed_ms,
        }
