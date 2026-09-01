"""Alert routes."""

from fastapi import APIRouter

from ..services.alerts import AlertListResponse, get_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="Active alerts",
    description="Return active impact-based alerts. Currently returns "
    "clearly-labelled demo alerts; the alert generation service arrives in a "
    "later stage.",
)
def alerts() -> AlertListResponse:
    return get_alerts()
