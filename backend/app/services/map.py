"""Risk grid (map) service (demo at this stage)."""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_risk_grid
from ..schemas.map import RiskGridResponse


class RiskGridResponseWrapper(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    data: RiskGridResponse


def get_risk_grid(
    latitude: float | None = None,
    longitude: float | None = None,
) -> RiskGridResponseWrapper:
    return RiskGridResponseWrapper(
        data=demo_risk_grid(latitude, longitude),
    )
