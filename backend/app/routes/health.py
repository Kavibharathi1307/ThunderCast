"""Health endpoint.

Provides liveness for the application and reports MongoDB connectivity
separately. The API stays alive even when the database is unreachable, and
never exposes credentials.

The database status is read from a background-thread cache so this handler
returns instantly — never blocking Render health-check probes.
"""

from fastapi import APIRouter

from ..database import warm_up_database_status
from ..services.health import get_database_status

# Ensure the background DB-probe daemon is started on first import.  Safe to
# call multiple times (no-op after the first).
warm_up_database_status()

router = APIRouter(tags=["Health"])


@router.get("/api/health", summary="Service health check")
def health():
    """Return service liveness and database connectivity status.

    - ``status`` is ``"healthy"`` whenever the process is running.
    - ``database`` is ``"connected"`` only after a successful background
      ping; otherwise ``"unavailable"`` (when Atlas is not configured or not
      reachable).
    """
    return {
        "status": "healthy",
        "service": "ThunderCast AI",
        "database": get_database_status(),
        "docs": "/docs",
        "health": "/api/health",
    }
