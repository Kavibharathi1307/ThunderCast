"""Weather service: current conditions.

Reads real Open-Meteo observations when real data is enabled, otherwise returns
clearly-labelled demo data. The ``demo`` flag in the response tells clients
which regime the data comes from.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..config import get_settings
from ..data.demo import DEMO_NOTE as DEMO_DATA_NOTE
from ..schemas.weather import WeatherObservation
from .weather_service import (
    DEMO_PROVENANCE,
    REAL_PROVENANCE,
    get_weather_observation,
)


class WeatherResponse(BaseModel):
    demo: bool = True
    demo_note: str | None = DEMO_DATA_NOTE
    environment_mode: str = "DEMO"
    data_provenance: str = "DEMO WEATHER DATA"
    data: WeatherObservation


def get_current_weather(latitude: float, longitude: float) -> WeatherResponse:
    settings = get_settings()
    mode = settings.ENVIRONMENT_MODE.upper()

    observation, is_real, provenance = get_weather_observation(latitude, longitude)

    # Real data is only surfaced when the environment is explicitly set to REAL
    # and the external API actually succeeded.
    is_real_response = is_real and mode == "REAL"
    return WeatherResponse(
        demo=not is_real_response,
        demo_note=DEMO_DATA_NOTE if not is_real_response else None,
        environment_mode="REAL" if is_real_response else "DEMO",
        data_provenance=REAL_PROVENANCE if is_real_response else DEMO_PROVENANCE,
        data=observation,
    )
