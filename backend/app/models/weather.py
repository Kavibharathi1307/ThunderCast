"""Persistence models for weather observations.

These define the document shape stored in the ``weather_observations``
collection. For now they map between PyMongo documents and the corresponding
Pydantic schemas; no scientific data is populated yet.
"""

from datetime import datetime

from bson import ObjectId

from ..schemas.weather import WeatherObservation
from .base import isoformat_utc


class WeatherObservationModel:
    """Helpers for the ``weather_observations`` collection."""

    @staticmethod
    def to_document(obs: WeatherObservation) -> dict:
        return {
            "latitude": obs.latitude,
            "longitude": obs.longitude,
            "timestamp": isoformat_utc(obs.timestamp),
            "temperature_c": obs.temperature_c,
            "humidity_percent": obs.humidity_percent,
            "wind_speed_ms": obs.wind_speed_ms,
            "wind_direction_deg": obs.wind_direction_deg,
            "pressure_hpa": obs.pressure_hpa,
            "precipitation_mm": obs.precipitation_mm,
            "source": obs.source,
        }

    @staticmethod
    def from_document(doc: dict) -> WeatherObservation:
        return WeatherObservation(
            latitude=doc["latitude"],
            longitude=doc["longitude"],
            timestamp=_parse_datetime(doc.get("timestamp")),
            temperature_c=doc.get("temperature_c"),
            humidity_percent=doc.get("humidity_percent"),
            wind_speed_ms=doc.get("wind_speed_ms"),
            wind_direction_deg=doc.get("wind_direction_deg"),
            pressure_hpa=doc.get("pressure_hpa"),
            precipitation_mm=doc.get("precipitation_mm"),
            source=doc.get("source"),
        )


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def object_id_to_str(value) -> str | None:
    if isinstance(value, ObjectId):
        return str(value)
    return value
