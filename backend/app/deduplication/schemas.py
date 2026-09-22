"""Pydantic schemas for Deduplication API and domain contracts."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MatchResult(BaseModel):
    """Detailed matching evaluation report between two job records."""

    model_config = ConfigDict(extra="ignore")

    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    match_type: str = Field(..., description="Classification of matching rule")
    matched_fields: Dict[str, float] = Field(
        default_factory=dict,
        description="Similarity scores broken down by component",
    )
    reason: str = Field(..., description="Explainable diagnostic rationale")


class JobDuplicateRead(BaseModel):
    """Schema for returning persisted JobDuplicate records."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    canonical_job_id: UUID
    duplicate_job_id: UUID
    match_type: str
    confidence_score: float
    matched_fields: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DedupStatusResponse(BaseModel):
    """Operational status and configuration parameters of Deduplication Engine."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool
    high_threshold: float
    medium_threshold: float
    max_candidates: int
    lookback_days: int


class DedupRunResponse(BaseModel):
    """Result of an on-demand deduplication analysis for a single job."""

    model_config = ConfigDict(extra="ignore")

    job_id: UUID
    is_duplicate: bool
    canonical_job_id: Optional[UUID] = None
    confidence_score: Optional[float] = None
    match_type: Optional[str] = None
    reason: str
