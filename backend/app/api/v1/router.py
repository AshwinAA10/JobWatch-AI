"""API v1 master router."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    ai,
    auth,
    dedup,
    health,
    matching,
    monitoring,
    notifications,
    profile,
    sources,
    jobs,
    applications,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["Candidate Profile"])
api_router.include_router(applications.router, prefix="/applications", tags=["Application Tracking"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications & Alerting"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs & Discovery"])
api_router.include_router(sources.router, tags=["Career Sources"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring Engine"])
api_router.include_router(dedup.router, prefix="/dedup", tags=["Deduplication Engine"])
api_router.include_router(matching.router, prefix="/matching", tags=["Matching Engine"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Intelligence"])
