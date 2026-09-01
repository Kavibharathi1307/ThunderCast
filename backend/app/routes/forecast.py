"""Forecast routes (0-6 hour nowcast points)."""

from fastapi import APIRouter

from ..schemas.common import Latitude, Longitude
from ..services.forecast import ForecastResponse, get_forecast
from ..utils.coordinates import parse_latitude, parse_longitude

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get(
    "/{latitude}/{longitude}",
    response_model=ForecastResponse,
    summary="0-6 hour nowcast forecast",
    description="Return probabilistic 0-6 hour forecast points (thunderstorm, "
    "hail, cloudburst) for a location. Currently returns clearly-labelled "
    "demo data; the ML nowcasting engine arrives in a later stage.",
)
def forecast(latitude: Latitude, longitude: Longitude) -> ForecastResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    return get_forecast(lat, lon)
