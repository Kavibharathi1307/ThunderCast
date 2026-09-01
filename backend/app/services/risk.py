"""Risk assessment service with explainable AI.

The service delegates to the rule-based risk engine (``ml/risk_engine``) to
compute thunderstorm / hail / cloudburst probabilities, overall risk level and
an explainable breakdown of contributing factors. Supporting inputs (demo
weather and the current lead-time forecast point) are attached for context.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_forecast, demo_weather
from ..ml.risk_engine import WeatherFeatures, assess_risk as engine_assess
from ..schemas.risk import RiskFactor, RiskResponse
from .intelligence import environment_mode, current_provenance


class RiskResponseWrapper(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO DATA"
    data: RiskResponse


def assess_risk(latitude: float, longitude: float) -> RiskResponseWrapper:
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
        environment_mode=environment_mode(),
        data_provenance=current_provenance(),
        data=data,
    )
