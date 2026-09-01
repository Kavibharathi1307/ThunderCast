"""Weather current-conditions routes."""

from fastapi import APIRouter, Query

from ..schemas.common import Latitude, Longitude
from ..services.weather import WeatherResponse, get_current_weather
from ..utils.coordinates import parse_latitude, parse_longitude

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get(
    "/current",
    response_model=WeatherResponse,
    summary="Current weather conditions",
    description="Return the current weather observation for a location. "
    "At this stage it returns clearly-labelled demo data; real "
    "observations will be provided by the ingestion layer in a later stage.",
)
def current_weather(
    latitude: Latitude = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    longitude: Longitude = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> WeatherResponse:
    lat = parse_latitude(latitude)
    lon = parse_longitude(longitude)
    return get_current_weather(lat, lon)
