"""Explainability and model-analytics routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..schemas.explainability import (
    ExplanationResponse,
    ModelAnalyticsResponse,
    DriverSchema,
)
from ..services.intelligence import (
    explain_risk_payload,
    explain_nowcast_payload,
    generate_nowcast_response,
    model_analytics,
)
from ..utils.coordinates import parse_latitude, parse_longitude

router = APIRouter(tags=["Intelligence"])


@router.get(
    "/api/explainability",
    response_model=ExplanationResponse,
    summary="Explain current risk at a location",
    description="Return a structured explanation of why a location currently "
    "has its assigned risk level (positive drivers, reducing factors, "
    "confidence).",
)
def explainability(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> ExplanationResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    payload = explain_risk_payload(lat, lon)
    return _to_schema(payload)


@router.get(
    "/api/explainability/{latitude}/{longitude}",
    response_model=ExplanationResponse,
    summary="Explain current risk at a location (path params)",
)
def explainability_by_path(latitude: float, longitude: float) -> ExplanationResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    payload = explain_risk_payload(lat, lon)
    return _to_schema(payload)


@router.get(
    "/api/explainability/nowcast",
    response_model=ExplanationResponse,
    summary="Explain 0-6 hour nowcast",
    description="Explain the peak-risk behaviour of the 0-6 hour nowcast at a "
    "location.",
)
def explain_nowcast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> ExplanationResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    nowcast, _impacts = generate_nowcast_response(lat, lon)
    payload = explain_nowcast_payload(nowcast)
    return _to_schema(payload)


@router.get(
    "/api/analytics/model",
    response_model=ModelAnalyticsResponse,
    summary="Model / evaluation analytics",
    description="Return an honest report of the current model: architecture, "
    "data provenance, and evaluation status (dataset_required until a real "
    "labelled dataset is supplied).",
)
def model_analytics_endpoint() -> ModelAnalyticsResponse:
    data = model_analytics()
    return ModelAnalyticsResponse(
        model_label=data["model_label"],
        model_version=data["model_version"],
        architecture=data["architecture"],
        evaluation=data["evaluation"],
        model_status=data["model_status"],
        environment_mode=data["environment_mode"],
        data_provenance=data["data_provenance"],
        model_name=data["model_name"],
        dataset=data["dataset"],
        targets=data["targets"],
        unavailable_targets=data["unavailable_targets"],
        feature_count=data["feature_count"],
        features=data["features"],
        training_samples=data["training_samples"],
        validation_samples=data["validation_samples"],
        test_samples=data["test_samples"],
        metrics=data["metrics"],
        limitations=data["limitations"],
    )


def _to_schema(payload) -> ExplanationResponse:
    return ExplanationResponse(
        prediction_type=payload.prediction_type,
        risk_level=payload.risk_level,
        summary=payload.summary,
        drivers=[
            DriverSchema(
                factor=d.factor,
                role=d.role,
                impact=d.impact,
                contribution=d.contribution,
                description=d.description,
            )
            for d in payload.drivers
        ],
        positive_drivers=payload.positive_drivers,
        reducing_factors=payload.reducing_factors,
        confidence=payload.confidence,
        model_label=payload.model_label,
        model_version=payload.model_version,
    )
