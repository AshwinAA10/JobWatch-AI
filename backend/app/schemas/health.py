"""Health check request and response schemas."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema representing application health check status."""

    status: str = Field(..., description="Application operational status", example="healthy")
    app_name: str = Field(..., description="Application name", example="JobWatch AI")
    version: str = Field(..., description="Application version", example="0.1.0")
    environment: str = Field(..., description="Current running environment", example="development")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the health check in UTC",
    )
