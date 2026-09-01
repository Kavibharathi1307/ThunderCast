"""ThunderCast AI backend application entry point.

FastAPI app wiring: CORS, routers, error handling, Swagger docs, and the
health endpoint. The application is designed to start even when MongoDB
Atlas is unavailable -- database connectivity is reported via /api/health
rather than required at startup.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .config import get_settings
from .routes import (
    alerts,
    explainability,
    forecast,
    health,
    historical,
    map,
    nowcast,
    risk,
    storm,
    weather,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("thundercast")

settings = get_settings()

app = FastAPI(
    title="ThunderCast AI API",
    description=(
        "Backend API for ThunderCast AI -- convective-scale nowcasting for "
        "thunderstorms, hail and cloudbursts (0-6 hr). At Stage 1 all data "
        "endpoints return clearly-labelled demo responses; the database, ML "
        "and alerting layers arrive in later stages."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS -- origins come from FRONTEND_URL (config). Never a bare "*" in
# production; localhost origins are added automatically in development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Return a clean 422 for uncaught pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.get("/", summary="Root", include_in_schema=False)
async def root() -> dict:
    return {"service": "ThunderCast AI", "docs": "/docs", "health": "/api/health"}


app.include_router(health.router)
app.include_router(weather.router)
app.include_router(forecast.router)
app.include_router(risk.router)
app.include_router(alerts.router)
app.include_router(historical.router)
app.include_router(map.router)
app.include_router(storm.router)
app.include_router(nowcast.router)
app.include_router(explainability.router)
