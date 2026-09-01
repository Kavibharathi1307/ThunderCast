"""Coordinate validation helpers.

FastAPI path parameters arrive as strings, so we validate and convert them
explicitly here to return clean HTTP 422 errors for out-of-range values.
"""

from fastapi import HTTPException, status


def parse_latitude(value: float) -> float:
    """Validate and return a latitude, raising HTTP 422 if out of range."""
    if not -90.0 <= value <= 90.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="latitude must be between -90 and 90",
        )
    return value


def parse_longitude(value: float) -> float:
    """Validate and return a longitude, raising HTTP 422 if out of range."""
    if not -180.0 <= value <= 180.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="longitude must be between -180 and 180",
        )
    return value
