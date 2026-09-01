"""Historical events service."""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_historical_events, demo_historical_analytics
from ..schemas.historical import HistoricalEvent
from ..schemas.analytics import HistoricalAnalytics


class HistoricalEventListResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    count: int
    events: list[HistoricalEvent]


class HistoricalAnalyticsResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    data: HistoricalAnalytics


def get_historical_events() -> HistoricalEventListResponse:
    events = demo_historical_events()
    return HistoricalEventListResponse(count=len(events), events=events)


def get_historical_analytics() -> HistoricalAnalyticsResponse:
    return HistoricalAnalyticsResponse(data=demo_historical_analytics())
