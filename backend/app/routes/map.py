"""Map / risk-grid routes."""

from fastapi import APIRouter, Query

from ..schemas.common import Latitude, Longitude
from ..services.map import RiskGridResponseWrapper, get_risk_grid

router = APIRouter(prefix="/api/map", tags=["Map"])


@router.get(
    "/risk-grid",
    response_model=RiskGridResponseWrapper,
    summary="Geographic risk grid",
    description="Return a grid of risk cells covering a region for geographic "
    "visualisation. When latitude/longitude are provided the grid is centred on "
    "that location so the map follows the selected city. Currently returns "
    "clearly-labelled demo cells; the geospatial risk layer arrives in a later "
    "stage.",
)
def risk_grid(
    latitude: Latitude | None = Query(
        default=None, ge=-90, le=90, description="Optional centre latitude"
    ),
    longitude: Longitude | None = Query(
        default=None, ge=-180, le=180, description="Optional centre longitude"
    ),
) -> RiskGridResponseWrapper:
    return get_risk_grid(latitude, longitude)
