"""AI intelligence API endpoints for job extraction and intelligence operations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.ai.cost.tracker import ai_cost_tracker
from app.ai.service import AIIntelligenceService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai import (
    AIJobRequirements,
    JobExtractionResponse,
    SemanticSearchResult,
    SimilarJobItem,
    SkillGapResponse,
)
from app.services.exceptions import JobNotFoundError, ProfileNotFoundError

router = APIRouter()


@router.post(
    "/jobs/{job_id}/extract",
    response_model=JobExtractionResponse,
    summary="Extract Structured Job Requirements",
    description="Invokes LLM extraction to extract structured criteria from raw job description.",
)
def extract_job_requirements(
    job_id: UUID,
    force_refresh: bool = Query(False, description="Force re-extraction ignoring existing cache"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobExtractionResponse:
    """Trigger or refresh AI requirements extraction for a job opening."""
    ai_service = AIIntelligenceService(db)
    try:
        extracted = ai_service.extract_job_requirements(job_id=job_id, force_refresh=force_refresh)
        cached_record = ai_service.get_cached_job_extraction(job_id=job_id)
        if not cached_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Extraction failed to produce an audit record.",
            )

        structured = (
            AIJobRequirements.model_validate(cached_record.structured_requirements)
            if cached_record.structured_requirements
            else None
        )

        return JobExtractionResponse(
            job_id=cached_record.job_id,
            input_hash=cached_record.input_hash,
            model=cached_record.model,
            prompt_version=cached_record.prompt_version,
            extraction_version=cached_record.extraction_version,
            is_success=cached_record.is_success,
            error_message=cached_record.error_message,
            structured_requirements=structured,
            created_at=cached_record.created_at,
        )
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )


@router.get(
    "/jobs/{job_id}/extraction",
    response_model=JobExtractionResponse,
    summary="Get Cached Job Extraction",
    description="Retrieves previously cached AI extraction record for a job opening.",
)
def get_job_extraction(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobExtractionResponse:
    """Retrieve existing extraction for a job."""
    ai_service = AIIntelligenceService(db)
    cached_record = ai_service.get_cached_job_extraction(job_id=job_id)
    if not cached_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI extraction found for this job. Trigger POST /ai/jobs/{job_id}/extract first.",
        )

    structured = (
        AIJobRequirements.model_validate(cached_record.structured_requirements)
        if cached_record.structured_requirements
        else None
    )

    return JobExtractionResponse(
        job_id=cached_record.job_id,
        input_hash=cached_record.input_hash,
        model=cached_record.model,
        prompt_version=cached_record.prompt_version,
        extraction_version=cached_record.extraction_version,
        is_success=cached_record.is_success,
        error_message=cached_record.error_message,
        structured_requirements=structured,
        created_at=cached_record.created_at,
    )


@router.get(
    "/jobs/{job_id}/skill-gaps",
    response_model=SkillGapResponse,
    summary="Candidate Skill Gap Analysis",
    description="Analyzes required and preferred skills against candidate profile, detecting exact and transferable skill coverage.",
)
def get_candidate_skill_gaps(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SkillGapResponse:
    """Analyze skill gaps and transferable skills between candidate and job."""
    ai_service = AIIntelligenceService(db)
    try:
        gap_data = ai_service.analyze_skill_gaps(user_id=current_user.id, job_id=job_id)
        return SkillGapResponse(**gap_data)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    except ProfileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")


@router.get(
    "/jobs/search/semantic",
    response_model=List[SemanticSearchResult],
    summary="Semantic Natural Language Job Search",
    description="Searches active job opportunities using query vector similarity with structured filters.",
)
def semantic_search_jobs(
    q: Optional[str] = Query(None, description="Natural language search query"),
    query: Optional[str] = Query(None, description="Alternative alias for natural language query"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
    workplace_type: Optional[str] = Query(None, description="Optional workplace filter (REMOTE, HYBRID, ONSITE)"),
    location: Optional[str] = Query(None, description="Optional location filter"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SemanticSearchResult]:
    """Execute natural language semantic search."""
    search_query = (q or query or "").strip()
    if len(search_query) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query ('q' or 'query') must be at least 2 characters long.",
        )
    ai_service = AIIntelligenceService(db)
    results = ai_service.semantic_search_jobs(
        query=search_query,
        limit=limit,
        workplace_type=workplace_type,
        location=location,
    )
    return [SemanticSearchResult(**r) for r in results]


@router.get(
    "/jobs/{job_id}/similar",
    response_model=List[SimilarJobItem],
    summary="Discover Similar Jobs",
    description="Discovers adjacent or similar job opportunities based on semantic vector similarity.",
)
def get_similar_jobs(
    job_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Max similar jobs"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SimilarJobItem]:
    """Retrieve similar career opportunities matching job profile."""
    ai_service = AIIntelligenceService(db)
    results = ai_service.find_similar_jobs(job_id=job_id, limit=limit)
    return [SimilarJobItem(**r) for r in results]


@router.get(
    "/telemetry/cost",
    summary="AI Cost and Telemetry Summary",
    description="Returns token usage, estimated cost, and cache efficiency metrics for AI operations.",
)
def get_ai_cost_telemetry(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve AI operational cost and cache telemetry."""
    return ai_cost_tracker.get_summary()
