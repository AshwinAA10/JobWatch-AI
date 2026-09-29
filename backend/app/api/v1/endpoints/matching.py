"""Matching API endpoints for evaluating and querying candidate-job compatibility."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.matching import (
    JobMatchResponse,
    JobRequirementsCreate,
    JobRequirementsResponse,
)
from app.services.exceptions import JobNotFoundError, ProfileNotFoundError
from app.services.matching import MatchingService

router = APIRouter()


@router.post(
    "/jobs/{job_id}",
    response_model=JobMatchResponse,
    summary="Match Candidate to Job",
    description="Evaluates deterministic matching between the authenticated candidate's profile and the specified job.",
)
def match_candidate_to_job(
    job_id: UUID,
    persist: bool = Query(True, description="Whether to persist the match result"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    """Trigger deterministic match evaluation for the authenticated user."""
    service = MatchingService(db)
    try:
        return service.match_candidate_to_job(
            user_id=current_user.id,
            job_id=job_id,
            persist=persist,
        )
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found. Please complete profile setup first.",
        )
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobMatchResponse,
    summary="Get Match Result for Job",
    description="Retrieves a previously computed match result for the authenticated user and job.",
)
def get_match_result(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobMatchResponse:
    """Retrieve existing match record for user and job."""
    service = MatchingService(db)
    try:
        match = service.get_match(user_id=current_user.id, job_id=job_id)
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match has not been evaluated for this job yet. POST to /jobs/{job_id} first.",
            )
        return JobMatchResponse.model_validate(match)
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )


@router.get(
    "/matches",
    response_model=List[JobMatchResponse],
    summary="List Matches for Current User",
    description="Lists all calculated job matches for the authenticated user ordered by score descending.",
)
def list_matches(
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum match score filter"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[JobMatchResponse]:
    """Retrieve match history for the authenticated user."""
    service = MatchingService(db)
    try:
        matches = service.list_matches_for_user(
            user_id=current_user.id,
            min_score=min_score,
            skip=skip,
            limit=limit,
        )
        return [JobMatchResponse.model_validate(m) for m in matches]
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found.",
        )


@router.put(
    "/jobs/{job_id}/requirements",
    response_model=JobRequirementsResponse,
    summary="Set Structured Job Requirements",
    description="Sets or updates structured requirements (skills, experience, salary, education) for a job.",
)
def set_job_requirements(
    job_id: UUID,
    requirements_data: JobRequirementsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobRequirementsResponse:
    """Set job requirements."""
    service = MatchingService(db)
    try:
        req = service.set_job_requirements(job_id=job_id, data=requirements_data)
        return JobRequirementsResponse.model_validate(req)
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )


@router.get(
    "/jobs/{job_id}/requirements",
    response_model=JobRequirementsResponse,
    summary="Get Structured Job Requirements",
    description="Retrieves structured requirements for a job opening.",
)
def get_job_requirements(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobRequirementsResponse:
    """Get job requirements."""
    service = MatchingService(db)
    try:
        req = service.get_job_requirements(job_id=job_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No structured requirements found for this job.",
            )
        return JobRequirementsResponse.model_validate(req)
    except JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )
