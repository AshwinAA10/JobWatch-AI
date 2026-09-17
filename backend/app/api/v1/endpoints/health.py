"""Health and readiness check endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import Settings, get_settings
from app.core.database import check_database_health
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health Check",
    description="Returns the process operational status, application version, and environment.",
    tags=["System"],
)
def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Check process health status of the application."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealthResponse,
    summary="Database Readiness Check",
    description="Validates active connectivity to the database with a lightweight SELECT 1 probe.",
    tags=["System"],
)
def get_db_health() -> DatabaseHealthResponse:
    """Probe database connectivity and report readiness."""
    is_healthy, latency_ms, error = check_database_health()
    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": error or "Database connection unavailable",
            },
        )
    return DatabaseHealthResponse(
        status="healthy",
        database="connected",
        latency_ms=latency_ms,
    )
