"""Pydantic schemas for Monitoring Engine requests, responses, and DTOs."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, computed_field


class MonitoringRunRead(BaseModel):
    """Schema for serialized MonitoringRun responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    career_source_id: UUID
    status: str
    trigger_type: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jobs_fetched: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    jobs_skipped: int = 0
    error_count: int = 0
    error_message: Optional[str] = None
    attempt: int = 1
    created_at: datetime
    updated_at: datetime

    @computed_field
    def duration_seconds(self) -> Optional[float]:
        """Calculate run duration in seconds if started and completed."""
        if self.started_at and self.completed_at:
            return round((self.completed_at - self.started_at).total_seconds(), 3)
        return None


class MonitoringStatusResponse(BaseModel):
    """Schema for monitoring scheduler and worker status."""

    model_config = ConfigDict(from_attributes=True)

    enabled: bool = Field(..., description="Whether background monitoring is globally enabled")
    running: bool = Field(..., description="Whether the in-process scheduler loop is actively running")
    interval_seconds: int = Field(..., description="Scheduled execution interval in seconds")
    max_concurrency: int = Field(..., description="Maximum concurrent source executions")
    active_sources_count: int = Field(..., description="Number of career sources currently being monitored")
    last_run_at: Optional[datetime] = Field(None, description="Timestamp of the most recently triggered schedule cycle")
    next_run_at: Optional[datetime] = Field(None, description="Timestamp of the next expected schedule cycle")


class MonitoringTriggerResponse(BaseModel):
    """Schema returned when manually triggering a career source run."""

    source_id: UUID
    run_id: Optional[UUID] = None
    status: str
    message: str


class MonitoringBatchTriggerResponse(BaseModel):
    """Schema returned when triggering all active career sources."""

    triggered_count: int
    skipped_count: int
    sources_triggered: List[UUID]
    sources_skipped: List[UUID]
    message: str
