"""Pydantic schemas for historical analytics."""

from pydantic import BaseModel, ConfigDict, Field

from .common import Probability


class EventTypeBreakdown(BaseModel):
    """Count of events by type."""

    model_config = ConfigDict(extra="forbid")

    thunderstorm: int = 0
    hail: int = 0
    cloudburst: int = 0


class RiskDistribution(BaseModel):
    """Distribution of events by risk level."""

    model_config = ConfigDict(extra="forbid")

    low: int = 0
    moderate: int = 0
    high: int = 0
    extreme: int = 0


class MonthlyTrend(BaseModel):
    """Monthly event count for trend analysis."""

    model_config = ConfigDict(extra="forbid")

    month: str
    count: int


class HistoricalAnalytics(BaseModel):
    """Aggregated analytics from historical data."""

    model_config = ConfigDict(extra="forbid")

    total_events: int
    date_range_start: str
    date_range_end: str
    event_types: EventTypeBreakdown
    risk_distribution: RiskDistribution
    avg_confidence: Probability
    monthly_trends: list[MonthlyTrend]
    peak_activity_month: str
    most_affected_region: str
    total_events_analyzed: int
