"""Nowcasting, impact and storm-prediction routes (intelligence layer)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from ..data.demo import DEMO_NOTE
from ..schemas.common import Latitude, Longitude
from ..schemas.nowcast import NowcastResponse, ImpactResponse
from ..schemas.storm_prediction import StormPredictionResponse
from ..services.intelligence import (
    generate_nowcast_response,
    storm_predictions,
    environment_mode,
    current_provenance,
)
from ..utils.coordinates import parse_latitude, parse_longitude

router = APIRouter(tags=["Intelligence"])


@router.get(
    "/api/nowcast",
    response_model=NowcastResponse,
    summary="0-6 hour nowcast",
    description="Return a probabilistic 0-6 hour nowcast (thunderstorm, hail, "
    "cloudburst) for a location. Baseline/pseudo-ML model clearly labelled; "
    "demo data at this stage.",
)
def nowcast(
    latitude: Latitude = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: Longitude = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> NowcastResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    result, _impacts = generate_nowcast_response(lat, lon)
    return NowcastResponse(
        demo=True,
        demo_note=DEMO_NOTE,
        latitude=lat,
        longitude=lon,
        forecast_time=result.forecast_time,
        window_hours=result.window_hours,
        peak_risk=result.peak_risk,
        peak_hour=result.peak_hour,
        risk_start_hour=result.risk_start_hour,
        risk_end_hour=result.risk_end_hour,
        model_label=result.model_label,
        model_version=result.model_version,
        environment_mode=environment_mode(),
        data_provenance=current_provenance(),
        points=[
            {
                "latitude": p.latitude,
                "longitude": p.longitude,
                "forecast_time": p.forecast_time,
                "horizon_hours": p.horizon_hours,
                "thunderstorm_probability": p.thunderstorm_probability,
                "hail_probability": p.hail_probability,
                "cloudburst_probability": p.cloudburst_probability,
                "overall_risk": p.overall_risk,
                "confidence": p.confidence,
                "model_label": p.model_label,
                "model_version": p.model_version,
            }
            for p in result.points
        ],
    )


@router.get(
    "/api/nowcast/{latitude}/{longitude}",
    response_model=NowcastResponse,
    summary="0-6 hour nowcast (path params)",
    description="Path-parameter variant of /api/nowcast.",
    include_in_schema=True,
)
def nowcast_by_path(latitude: Latitude, longitude: Longitude) -> NowcastResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    return nowcast(latitude=lat, longitude=lon)


@router.get(
    "/api/forecast/timeline",
    response_model=NowcastResponse,
    summary="0-6 hour nowcast timeline",
    description="Alias of /api/nowcast returning the 0-6h timeline for the "
    "Forecast page.",
)
def forecast_timeline(
    latitude: Latitude = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: Longitude = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> NowcastResponse:
    return nowcast(latitude=latitude, longitude=longitude)


@router.get(
    "/api/impact",
    response_model=ImpactResponse,
    summary="Impact-based risk scores",
    description="Return prototype impact scores (flooding, roads, agriculture, "
    "waterlogging, lightning, hail, visibility) for a location, each 0..1. "
    "Clearly labelled as a prototype impact model.",
)
def impact(
    latitude: Latitude = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: Longitude = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> ImpactResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    _result, impacts = generate_nowcast_response(lat, lon)
    return ImpactResponse(
        demo=True,
        demo_note=DEMO_NOTE,
        latitude=lat,
        longitude=lon,
        label=impacts.label,
        impacts=impacts.as_dict(),
    )


@router.get(
    "/api/storms/predictions",
    response_model=StormPredictionResponse,
    summary="Storm movement predictions",
    description="Return baseline storm-motion extrapolation predictions (30/60/"
    "90/120 min) for detected storm cells. Clearly labelled baseline method.",
)
def storm_motion_predictions() -> StormPredictionResponse:
    predictions = storm_predictions()
    return StormPredictionResponse(
        demo=True,
        demo_note=DEMO_NOTE,
        count=len(predictions),
        predictions=[
            {
                "cell_id": p.cell_id,
                "current_latitude": p.current_latitude,
                "current_longitude": p.current_longitude,
                "movement_direction_deg": p.movement_direction_deg,
                "movement_speed_kmh": p.movement_speed_kmh,
                "current_intensity": p.current_intensity,
                "label": p.label,
                "predicted_positions": [
                    {
                        "latitude": pos.latitude,
                        "longitude": pos.longitude,
                        "valid_time": pos.valid_time,
                        "minutes_ahead": pos.minutes_ahead,
                        "intensity": pos.intensity,
                    }
                    for pos in p.predicted_positions
                ],
            }
            for p in predictions
        ],
    )
