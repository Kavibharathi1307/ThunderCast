"""Alert service with impact-based alerts."""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_alerts
from ..schemas.alerts import Alert


class AlertListResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    count: int
    alerts: list[Alert]


def get_alerts() -> AlertListResponse:
    alerts = demo_alerts()
    return AlertListResponse(count=len(alerts), alerts=alerts)
