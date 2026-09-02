"""Application configuration loaded from environment variables.

All configuration values come from environment variables (or the local
``.env`` file in development). No secrets or production URLs are ever
hardcoded here.
"""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed access to environment configuration.

    Values are read from the process environment and, when present, the
    ``.env`` file located alongside this module (``backend/.env``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # MongoDB Atlas connection string. Leave empty if not configured; the
    # backend must still start and serve endpoints such as /api/health.
    MONGO_URI: str = ""

    # Comma-separated list of allowed frontend origins. Corresponds to the
    # FRONTEND_URL environment variable. Defaults to a localhost origin for
    # local development convenience.
    FRONTEND_URL: str = "http://localhost:5173"

    ENVIRONMENT: str = "development"

    # Data mode: "DEMO" or "REAL".
    # * DEMO: use the deterministic DemoDataProvider (no network calls).
    # * REAL: use the live weather providers (Open-Meteo) for real observations.
    # The mode is surfaced in API responses via ``environment_mode`` so the app
    # never silently mixes demo and real data. REAL mode degrades gracefully to
    # DEMO when a provider is offline or the feature is disabled.
    #
    # Production defaults to REAL; local/development defaults to DEMO so tests
    # and offline development never hit the network. Either can be overridden
    # with the ENVIRONMENT_MODE environment variable.
    ENVIRONMENT_MODE: str | None = None

    # Whether the real providers are allowed to make outbound network calls.
    # Kept behind a flag so tests and offline environments never hit the network.
    # Defaults to enabled in production, disabled in development, and can be
    # overridden with the ALLOW_EXTERNAL_API environment variable.
    ALLOW_EXTERNAL_API: bool | None = None

    @model_validator(mode="after")
    def _apply_environment_defaults(self):
        """Make REAL mode + outbound API the production defaults while keeping
        both fully configurable via environment variables."""
        production = self.ENVIRONMENT.lower() == "production"
        if self.ENVIRONMENT_MODE is None:
            self.ENVIRONMENT_MODE = "REAL" if production else "DEMO"
        if self.ALLOW_EXTERNAL_API is None:
            self.ALLOW_EXTERNAL_API = production
        return self

    # Open-Meteo base URLs (free, no API key required). Overridable so tests can
    # point at a local/mock server without modifying code.
    OPEN_METEO_FORECAST_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1/archive"

    # Persisted trained-model filename within the backend model directory.
    MODEL_STORE_FILE: str = "thundercast_model.json"

    # Database used within MongoDB Atlas. Kept configurable so a single app
    # can target different clusters/databases without code changes.
    MONGO_DB_NAME: str = "thundercast"

    # Collection names used by the application.
    COLLECTION_WEATHER_OBSERVATIONS: str = "weather_observations"
    COLLECTION_FORECASTS: str = "forecasts"
    COLLECTION_RISK_ASSESSMENTS: str = "risk_assessments"
    COLLECTION_ALERTS: str = "alerts"
    COLLECTION_HISTORICAL_EVENTS: str = "historical_events"

    # Connection tuning for PyMongo. Short serverSelectionTimeoutMS keeps the
    # backend responsive (and startable) when Atlas is temporarily unreachable.
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 3000
    MONGO_CONNECT_TIMEOUT_MS: int = 3000

    @property
    def cors_origins(self) -> list[str]:
        """Origins allowed to call the API via CORS."""
        origins = [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]
        if self.ENVIRONMENT == "development":
            origins += [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        # De-duplicate while preserving order.
        return list(dict.fromkeys(origins))


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
