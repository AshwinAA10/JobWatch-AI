"""AI intelligence API endpoints for job extraction and intelligence operations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.ai.service import AIIntelligenceService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai import AIJobRequirements, JobExtractionResponse
from app.services.exceptions import JobNotFoundError

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
