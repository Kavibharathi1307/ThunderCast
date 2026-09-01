"""Weather service: current conditions.

At this stage it returns clearly-labelled demo data. When a database is
available, the response includes a ``demo`` flag and note so clients can
distinguish contract-test data from real observations (which arrive later).
"""

from __future__ import annotations

from pydantic import BaseModel

from ..data.demo import DEMO_NOTE, demo_weather
from ..schemas.weather import WeatherObservation


class WeatherResponse(BaseModel):
    demo: bool = True
    demo_note: str = DEMO_NOTE
    data: WeatherObservation


def get_current_weather(latitude: float, longitude: float) -> WeatherResponse:
    return WeatherResponse(data=demo_weather(latitude, longitude))
