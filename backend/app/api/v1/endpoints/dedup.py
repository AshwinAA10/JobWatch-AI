"""Deduplication API endpoints (Phase 4)."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.deduplication.exceptions import JobNotFoundError
from app.deduplication.schemas import (
    DedupRunResponse,
    DedupStatusResponse,
    JobDuplicateRead,
)
from app.deduplication.service import DeduplicationService
from app.repositories.job_duplicate import JobDuplicateRepository

router = APIRouter()
settings = get_settings()


@router.get(
    "/status",
    response_model=DedupStatusResponse,
    summary="Get Deduplication Engine Status",
    description="Inspect whether the deduplication engine is active and view current threshold configurations.",
)
def get_dedup_status() -> DedupStatusResponse:
    """Return deduplication engine operational configuration."""
    return DedupStatusResponse(
        enabled=settings.DEDUP_ENABLED,
        high_threshold=settings.DEDUP_HIGH_THRESHOLD,
        medium_threshold=settings.DEDUP_MEDIUM_THRESHOLD,
        max_candidates=settings.DEDUP_MAX_CANDIDATES,
        lookback_days=settings.DEDUP_LOOKBACK_DAYS,
    )


@router.get(
    "/duplicates",
    response_model=List[JobDuplicateRead],
    summary="List Duplicate Relationships",
    description="Query historical job duplicate records with optional canonical ID filtering and pagination.",
)
def list_duplicates(
    canonical_id: Optional[UUID] = Query(None, description="Filter by canonical job UUID"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
) -> List[JobDuplicateRead]:
    """Return historical duplicate relationships ordered newest first."""
    repo = JobDuplicateRepository(db)
    duplicates = repo.list_duplicates(skip=skip, limit=limit, canonical_id=canonical_id)
    return [JobDuplicateRead.model_validate(d) for d in duplicates]


@router.post(
    "/run/{job_id}",
    response_model=DedupRunResponse,
    summary="Trigger Deduplication for Single Job",
    description="Manually evaluate duplicate candidates for a specific job and establish a canonical link if confidence meets threshold.",
)
def run_job_deduplication(
    job_id: UUID,
    db: Session = Depends(get_db),
) -> DedupRunResponse:
    """Evaluate and link duplicates for a given job ID."""
    service = DeduplicationService(db)
    try:
        dup = service.deduplicate_job(job_id)
        if dup:
            return DedupRunResponse(
                job_id=job_id,
                is_duplicate=True,
                canonical_job_id=dup.canonical_job_id,
                confidence_score=dup.confidence_score,
                match_type=dup.match_type,
                reason=dup.reason or "High confidence duplicate match found",
            )
        return DedupRunResponse(
            job_id=job_id,
            is_duplicate=False,
            reason="No duplicate matching above confidence threshold found",
        )
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
