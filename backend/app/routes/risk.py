"""Risk assessment routes."""

from fastapi import APIRouter

from ..schemas.common import Latitude, Longitude
from ..services.risk import RiskResponseWrapper, assess_risk
from ..utils.coordinates import parse_latitude, parse_longitude

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.get(
    "/{latitude}/{longitude}",
    response_model=RiskResponseWrapper,
    summary="Convective risk assessment",
    description="Return a risk assessment (thunderstorm / hail / cloudburst "
    "probabilities, overall risk level and confidence) for a location. "
    "The rule-based risk engine computes the assessment from weather features; "
    "supporting inputs are currently demo data.",
)
def risk(latitude: Latitude, longitude: Longitude) -> RiskResponseWrapper:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    return assess_risk(lat, lon)
