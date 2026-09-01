"""Historical analytics routes."""

from fastapi import APIRouter

from ..services.historical import (
    HistoricalEventListResponse,
    HistoricalAnalyticsResponse,
    get_historical_events,
    get_historical_analytics,
)

router = APIRouter(prefix="/api/historical", tags=["Historical"])


@router.get(
    "",
    response_model=HistoricalEventListResponse,
    summary="Historical convective events",
    description="Return a list of recorded historical convective events. "
    "Currently returns clearly-labelled demo records.",
)
def historical() -> HistoricalEventListResponse:
    return get_historical_events()


@router.get(
    "/analytics",
    response_model=HistoricalAnalyticsResponse,
    summary="Historical analytics and trends",
    description="Return aggregated analytics from historical data including "
    "event type breakdown, risk distribution, monthly trends, and peak activity. "
    "Currently returns clearly-labelled demo data.",
)
def historical_analytics() -> HistoricalAnalyticsResponse:
    return get_historical_analytics()
