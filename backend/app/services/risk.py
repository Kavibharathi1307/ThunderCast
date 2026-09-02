"""Risk assessment service with explainable AI.

The service delegates to the rule-based risk engine (``ml/risk_engine``) to
compute thunderstorm / hail / cloudburst probabilities, overall risk level and
an explainable breakdown of contributing factors. When real weather data is
enabled (REAL mode + external API allowed), the engine receives real Open-Meteo
variables; otherwise it falls back to demo weather. The ``demo`` flag and
``environment_mode`` field clearly label which regime the output came from.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..config import get_settings
from ..data.demo import DEMO_NOTE, demo_forecast, demo_weather
from ..ml.risk_engine import WeatherFeatures, assess_risk as engine_assess
from ..schemas.risk import RiskFactor, RiskResponse
from .weather_service import (
    REAL_PROVENANCE,
    get_weather_observation,
)


class RiskResponseWrapper(BaseModel):
    demo: bool = True
    demo_note: str | None = DEMO_NOTE
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO DATA"
    data: RiskResponse


def assess_risk(latitude: float, longitude: float) -> RiskResponseWrapper:
    settings = get_settings()
    mode = settings.ENVIRONMENT_MODE.upper()

    observation, is_real, _ = get_weather_observation(latitude, longitude)
    is_real_response = is_real and mode == "REAL"

    if is_real_response:
        weather = observation
        features = WeatherFeatures(
            latitude=latitude,
            longitude=longitude,
            temperature_c=weather.temperature_c if weather.temperature_c is not None else 29.0,
            humidity_percent=weather.humidity_percent or 70.0,
            wind_speed_ms=weather.wind_speed_ms or 5.0,
            wind_direction_deg=weather.wind_direction_deg or 180.0,
            pressure_hpa=weather.pressure_hpa or 1010.0,
            precipitation_mm=weather.precipitation_mm or 0.0,
        )
    else:
        weather = demo_weather(latitude, longitude)
        features = WeatherFeatures(
            latitude=latitude,
            longitude=longitude,
            temperature_c=weather.temperature_c,
            humidity_percent=weather.humidity_percent,
            wind_speed_ms=weather.wind_speed_ms,
            wind_direction_deg=weather.wind_direction_deg,
            pressure_hpa=weather.pressure_hpa,
            precipitation_mm=weather.precipitation_mm,
        )

    result = engine_assess(features)

    forecast_pts = demo_forecast(latitude, longitude)

    data = RiskResponse(
        latitude=latitude,
        longitude=longitude,
        timestamp=result.timestamp,
        thunderstorm_probability=result.thunderstorm_probability,
        hail_probability=result.hail_probability,
        cloudburst_probability=result.cloudburst_probability,
        overall_risk=result.overall_risk,
        confidence=result.confidence,
        explanation=result.explanation,
        risk_factors=[
            RiskFactor(
                name=f.name,
                contribution=f.contribution,
                description=f.description,
            )
            for f in result.factors
        ],
        weather=weather,
        forecast=forecast_pts[0] if forecast_pts else None,
    )
    return RiskResponseWrapper(
        demo=not is_real_response,
        demo_note=None if is_real_response else DEMO_NOTE,
        environment_mode="REAL" if is_real_response else "DEMO",
        data_provenance=REAL_PROVENANCE if is_real_response else "DEMO DATA",
        data=data,
    )
