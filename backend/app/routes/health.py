"""Health endpoint.

Provides liveness for the application and reports MongoDB connectivity
separately. The API stays alive even when the database is unreachable, and
never exposes credentials.
"""

from fastapi import APIRouter

from ..services.health import get_database_status

router = APIRouter(tags=["Health"])


@router.get("/api/health", summary="Service health check")
def health():
    """Return service liveness and database connectivity status.

    - ``status`` is ``"healthy"`` whenever the process is running.
    - ``database`` is ``"connected"`` only after a successful live ping;
      otherwise ``"unavailable"`` (when Atlas is not configured or not
      reachable).
    """
    return {
        "status": "healthy",
        "service": "ThunderCast AI",
        "database": get_database_status(),
    }
