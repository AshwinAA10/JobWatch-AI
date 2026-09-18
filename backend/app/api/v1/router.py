"""API v1 master router."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, sources

api_router = APIRouter()
api_router.include_router(health.router, tags=["System"])
api_router.include_router(sources.router, tags=["Career Sources"])
