"""JobWatch AI - Main FastAPI Application Entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.health import get_health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.schemas.health import HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="JobWatch AI - Automated Career Portal Monitoring & Opportunity Intelligence",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS Configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Root-level health check endpoint for container orchestrators and load balancers
app.add_api_route(
    "/health",
    get_health,
    methods=["GET"],
    response_model=HealthResponse,
    summary="Root Health Check",
    tags=["System"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["System"], include_in_schema=False)
def root_summary():
    """Root metadata response."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "phase": "Phase 0 - Architecture & Project Setup",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }
