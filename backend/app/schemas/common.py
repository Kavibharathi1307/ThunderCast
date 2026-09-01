"""Common Pydantic types shared across schemas."""

from typing import Annotated, Literal

from pydantic import Field


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Raise ValueError if lat/lon are outside valid ranges."""
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be between -90 and 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be between -180 and 180")


Latitude = Annotated[float, Field(ge=-90.0, le=90.0)]
Longitude = Annotated[float, Field(ge=-180.0, le=180.0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "EXTREME"]
