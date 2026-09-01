"""Map / risk-grid routes."""

from fastapi import APIRouter

from ..services.map import RiskGridResponseWrapper, get_risk_grid

router = APIRouter(prefix="/api/map", tags=["Map"])


@router.get(
    "/risk-grid",
    response_model=RiskGridResponseWrapper,
    summary="Geographic risk grid",
    description="Return a grid of risk cells covering a region for geographic "
    "visualisation. Currently returns clearly-labelled demo cells; the "
    "geospatial risk layer arrives in a later stage.",
)
def risk_grid() -> RiskGridResponseWrapper:
    return get_risk_grid()
