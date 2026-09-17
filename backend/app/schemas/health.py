"""Health check request and response schemas."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema representing application health check status."""

    status: str = Field(..., description="Application operational status", json_schema_extra={"example": "healthy"})
    app_name: str = Field(..., description="Application name", json_schema_extra={"example": "JobWatch AI"})
    version: str = Field(..., description="Application version", json_schema_extra={"example": "0.1.0"})
    environment: str = Field(..., description="Current running environment", json_schema_extra={"example": "development"})
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the health check in UTC",
    )


class DatabaseHealthResponse(BaseModel):
    """Schema representing database connectivity and readiness status."""

    status: str = Field(..., description="Readiness status", json_schema_extra={"example": "healthy"})
    database: str = Field(..., description="Database connectivity state", json_schema_extra={"example": "connected"})
    latency_ms: float = Field(..., description="Round-trip latency in milliseconds", json_schema_extra={"example": 1.45})
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the health probe in UTC",
    )
