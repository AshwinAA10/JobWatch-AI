"""FastAPI application entrypoint with production hardening, resilience, and lifecycle management."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.health import get_db_health, get_health, get_liveness, get_readiness
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.core.middleware import (
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from app.monitoring.scheduler import get_scheduler
from app.schemas.health import DatabaseHealthResponse, HealthResponse
from app.services.exceptions import DomainError

settings = get_settings()

# Initialize structured logging and sensitive data redaction
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger("jobwatch.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup validation and graceful shutdown."""
    # 1. Startup: Validate production configuration if running in production
    logger.info("Initializing JobWatch AI (%s - %s)", settings.APP_NAME, settings.APP_ENV)
    settings.validate_production_configuration()

    # 2. Startup: Start scheduler if monitoring enabled
    scheduler = get_scheduler()
    if settings.MONITORING_ENABLED:
        logger.info("Starting background monitoring scheduler...")
        await scheduler.start()

    yield

    # 3. Shutdown: Gracefully stop scheduler and release worker resources
    logger.info("Shutting down JobWatch AI background tasks...")
    await scheduler.stop()

    # 4. Shutdown: Dispose database connection pool cleanly
    logger.info("Disposing database connection pool...")
    engine.dispose()
    logger.info("JobWatch AI shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="JobWatch AI - Automated Career Portal Monitoring & Opportunity Intelligence",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Global Production Middlewares (Applied in order: Metrics -> RateLimit -> Security -> RequestID -> CORS)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS Configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Global Exception Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle standard HTTPExceptions preserving detail for existing clients and adding standard error wrapper."""
    req_id = getattr(request.state, "request_id", None)
    error_code = f"HTTP_{exc.status_code}"
    
    # If detail is already a dict (e.g. from health check failure), extract details cleanly
    if isinstance(exc.detail, dict):
        message = exc.detail.get("error") or exc.detail.get("status") or str(exc.detail)
    else:
        message = str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": error_code,
                "message": message,
                "request_id": req_id,
            },
        },
        headers=exc.headers or ({"X-Request-ID": req_id} if req_id else None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors cleanly without exposing internals."""
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "request_id": req_id,
            },
        },
        headers={"X-Request-ID": req_id} if req_id else None,
    )


@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    """Map domain exceptions to clean HTTP responses."""
    req_id = getattr(request.state, "request_id", None)
    logger.warning("Domain exception encountered: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.message,
            "error": {
                "code": exc.__class__.__name__,
                "message": exc.message,
                "request_id": req_id,
            },
        },
        headers={"X-Request-ID": req_id} if req_id else None,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler: sanitize in production, avoid leaking internals."""
    req_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled server exception: %s", str(exc))

    message = str(exc) if settings.DEBUG else "An unexpected internal server error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": message,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
                "request_id": req_id,
            },
        },
        headers={"X-Request-ID": req_id} if req_id else None,
    )


# Root-level health check endpoint for container orchestrators and load balancers
app.add_api_route(
    "/health",
    get_health,
    methods=["GET"],
    response_model=HealthResponse,
    summary="Root Process Health Check",
    tags=["System"],
)

app.add_api_route(
    "/health/live",
    get_liveness,
    methods=["GET"],
    response_model=HealthResponse,
    summary="Root Liveness Probe",
    tags=["System"],
)

# Root-level database readiness probe
app.add_api_route(
    "/health/ready",
    get_readiness,
    methods=["GET"],
    response_model=DatabaseHealthResponse,
    summary="Root Service Readiness Probe",
    tags=["System"],
)

app.add_api_route(
    "/health/db",
    get_db_health,
    methods=["GET"],
    response_model=DatabaseHealthResponse,
    summary="Root Database Readiness Check",
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
        "phase": "Phase 11 - Reliability & Production Hardening",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }
