"""API v1 master router."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, monitoring, sources

api_router = APIRouter()
api_router.include_router(health.router, tags=["System"])
api_router.include_router(sources.router, tags=["Career Sources"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring Engine"])
