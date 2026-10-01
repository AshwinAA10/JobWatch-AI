"""Job discovery, search, filtering, detail, and bookmark endpoints."""

import math
from typing import Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.models.user import User
from app.repositories.ai_explanation import AIExplanationRepository
from app.repositories.ai_job_extraction import AIJobExtractionRepository
from app.repositories.application import ApplicationRepository
from app.repositories.job import JobRepository
from app.repositories.job_duplicate import JobDuplicateRepository
from app.repositories.job_match import JobMatchRepository
from app.repositories.saved_job import SavedJobRepository
from app.schemas.job import (
    JobCardResponse,
    JobDetailResponse,
    JobListResponse,
    SavedJobResponse,
)
from app.services.profile import ProfileService

router = APIRouter()


def _build_job_card(
    job: Job,
    saved_ids: set,
    matches_by_job_id: Dict[UUID, any],
    applications_by_job_id: Optional[Dict[UUID, any]] = None,
) -> JobCardResponse:
    """Helper to convert Job ORM entity into JobCardResponse with match intelligence."""
    company_name = job.company.name if job.company else "Unknown Company"
    company_slug = job.company.slug if job.company else "unknown"
    source_name = job.career_source.name if job.career_source else None

    match = matches_by_job_id.get(job.id)
    app_record = applications_by_job_id.get(job.id) if applications_by_job_id else None

    return JobCardResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=company_name,
        company_slug=company_slug,
        career_source_name=source_name,
        title=job.title,
        location=job.location,
        employment_type=job.employment_type,
        workplace_type=job.workplace_type,
        application_url=job.application_url or job.source_url,
        posted_at=job.posted_at,
        first_seen_at=job.first_seen_at,
        canonical_job_id=job.canonical_job_id,
        is_active=job.is_active,
        match_score=float(match.score) if match else None,
        match_confidence=match.confidence if match else None,
        match_type="hybrid" if (match and getattr(match, "scoring_version", "").startswith("hybrid")) else ("deterministic" if match else None),
        match_reasons=match.reasons if (match and match.reasons) else [],
        is_saved=job.id in saved_ids,
        application_id=app_record.id if app_record else None,
        application_status=(app_record.status.value if hasattr(app_record.status, "value") else str(app_record.status)) if app_record else None,
    )


@router.get(
    "",
    response_model=JobListResponse,
    summary="Search & Discover Jobs",
    description="Paginated job search supporting keyword search, location, workplace type, company, and score filtering.",
)
def list_jobs(
    q: Optional[str] = Query(None, description="Search query matching title, company, or location"),
    location: Optional[str] = Query(None, description="Filter by location substring"),
    workplace_type: Optional[str] = Query(None, description="Filter by workplace type (remote, hybrid, on-site)"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (full-time, part-time, etc.)"),
    company_id: Optional[UUID] = Query(None, description="Filter by company ID"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Filter jobs with match score >= min_score"),
    sort_by: str = Query("newest", pattern="^(newest|recently_updated|best_match|title)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """Retrieve filtered, paginated jobs with candidate match scores and bookmark state."""
    job_repo = JobRepository(db)
    saved_repo = SavedJobRepository(db)
    match_repo = JobMatchRepository(db)
    app_repo = ApplicationRepository(db)

    # Resolve candidate profile if authenticated
    profile: Optional[CandidateProfile] = None
    saved_ids = set()
    matches_by_job_id: Dict[UUID, any] = {}
    apps_by_job_id: Dict[UUID, any] = {}

    if current_user:
        profile_service = ProfileService(db)
        profile = profile_service.get_or_create_profile(current_user.id)
        saved_ids = saved_repo.get_saved_job_ids(profile.id)

        user_matches = match_repo.list_for_profile(profile.id, limit=500)
        matches_by_job_id = {m.job_id: m for m in user_matches}

        user_apps, _ = app_repo.list_for_profile(profile.id, limit=500)
        apps_by_job_id = {a.job_id: a for a in user_apps if a.job_id}

    # Fetch jobs from repository
    skip = (page - 1) * page_size
    repo_sort = "newest" if sort_by == "best_match" else sort_by

    jobs, total = job_repo.search_and_filter(
        q=q,
        location=location,
        workplace_type=workplace_type,
        employment_type=employment_type,
        company_id=company_id,
        is_active=True,
        sort_by=repo_sort,
        skip=skip if sort_by != "best_match" else 0,
        limit=page_size if sort_by != "best_match" else 200,
    )

    # Build card models
    card_items = [_build_job_card(j, saved_ids, matches_by_job_id, apps_by_job_id) for j in jobs]

    # Filter by minimum match score if requested
    if min_score is not None:
        card_items = [c for c in card_items if c.match_score is not None and c.match_score >= min_score]
        total = len(card_items)

    # Sort by best match if requested
    if sort_by == "best_match":
        card_items.sort(key=lambda x: (x.match_score is not None, x.match_score or 0.0), reverse=True)
        total = len(card_items)
        card_items = card_items[skip : skip + page_size]

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return JobListResponse(
        items=card_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/saved",
    response_model=dict,
    summary="List Saved/Bookmarked Jobs",
    description="Retrieves the authenticated candidate's bookmarked job postings.",
)
def list_saved_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List bookmarked jobs for authenticated user."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    saved_repo = SavedJobRepository(db)
    match_repo = JobMatchRepository(db)

    skip = (page - 1) * page_size
    jobs, total = saved_repo.list_saved_for_profile(profile.id, skip=skip, limit=page_size)
    saved_ids = saved_repo.get_saved_job_ids(profile.id)

    app_repo = ApplicationRepository(db)
    user_apps, _ = app_repo.list_for_profile(profile.id, limit=500)
    apps_by_job_id = {a.job_id: a for a in user_apps if a.job_id}

    user_matches = match_repo.list_for_profile(profile.id, limit=500)
    matches_by_job_id = {m.job_id: m for m in user_matches}

    items = []
    for job in jobs:
        card = _build_job_card(job, saved_ids, matches_by_job_id, apps_by_job_id)
        saved_record = saved_repo.get_by_profile_and_job(profile.id, job.id)
        items.append(
            SavedJobResponse(
                id=saved_record.id if saved_record else job.id,
                profile_id=profile.id,
                job_id=job.id,
                notes=saved_record.notes if saved_record else None,
                created_at=saved_record.created_at if saved_record else job.first_seen_at,
                job=card,
            ).model_dump()
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get Job Details",
    description="Fetches full details of a job opening including requirements, company, matching breakdown, and AI insights.",
)
def get_job_detail(
    job_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> JobDetailResponse:
    """Retrieve full job detail by ID with candidate match and AI insights."""
    job_repo = JobRepository(db)
    job = job_repo.get_by_id_with_relations(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    # Basic card representation
    saved_repo = SavedJobRepository(db)
    match_repo = JobMatchRepository(db)
    explanation_repo = AIExplanationRepository(db)
    extraction_repo = AIJobExtractionRepository(db)
    duplicate_repo = JobDuplicateRepository(db)
    app_repo = ApplicationRepository(db)

    is_saved = False
    match = None
    ai_expl = None
    structured_reqs = None
    application = None

    if current_user:
        profile_service = ProfileService(db)
        profile = profile_service.get_or_create_profile(current_user.id)
        is_saved = saved_repo.is_saved(profile.id, job.id)
        match = match_repo.get_by_profile_and_job(profile.id, job.id)
        ai_expl = explanation_repo.get_by_profile_and_job(profile.id, job.id)
        application = app_repo.get_by_profile_and_job(profile.id, job.id)

    # Check cached extraction
    cached_extraction = extraction_repo.get_by_job_id(job.id)
    if cached_extraction and cached_extraction.structured_requirements:
        structured_reqs = cached_extraction.structured_requirements

    # Count duplicates
    canonical_id = job.canonical_job_id or job.id
    dup_records = duplicate_repo.get_duplicates_for_canonical(canonical_id)
    duplicate_count = len(dup_records)

    company_name = job.company.name if job.company else "Unknown Company"
    company_slug = job.company.slug if job.company else "unknown"
    source_name = job.career_source.name if job.career_source else None

    # Explanations / Insights
    ai_data = None
    if ai_expl:
        ai_data = {
            "narrative_summary": ai_expl.narrative_summary,
            "strengths": ai_expl.strengths,
            "gaps": ai_expl.gaps,
            "recommendations": ai_expl.recommendations,
            "is_ai_generated": True,
        }

    return JobDetailResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=company_name,
        company_slug=company_slug,
        career_source_name=source_name,
        title=job.title,
        description=job.description,
        location=job.location,
        employment_type=job.employment_type,
        workplace_type=job.workplace_type,
        application_url=job.application_url or job.source_url,
        source_url=job.source_url,
        posted_at=job.posted_at,
        first_seen_at=job.first_seen_at,
        canonical_job_id=job.canonical_job_id,
        is_active=job.is_active,
        match_score=float(match.score) if match else None,
        match_confidence=match.confidence if match else None,
        match_type="hybrid" if (match and getattr(match, "scoring_version", "").startswith("hybrid")) else ("deterministic" if match else None),
        match_reasons=match.reasons if (match and match.reasons) else [],
        matched_criteria=match.matched_criteria if (match and match.matched_criteria) else [],
        missing_criteria=match.missing_criteria if (match and match.missing_criteria) else [],
        breakdown=match.breakdown if (match and match.breakdown) else None,
        ai_explanation=ai_data,
        structured_requirements=structured_reqs,
        duplicate_count=duplicate_count,
        is_saved=is_saved,
        application_id=application.id if application else None,
        application_status=(application.status.value if hasattr(application.status, "value") else str(application.status)) if application else None,
    )


@router.post(
    "/{job_id}/save",
    summary="Save/Bookmark Job",
    description="Bookmarks a job posting for the authenticated candidate.",
)
def save_job(
    job_id: UUID,
    notes: Optional[str] = Query(None, description="Optional candidate notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Bookmark job for candidate."""
    job_repo = JobRepository(db)
    if not job_repo.get_by_id(job_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    saved_repo = SavedJobRepository(db)
    saved_repo.save_job(profile_id=profile.id, job_id=job_id, notes=notes)
    return {"status": "saved", "job_id": str(job_id)}


@router.delete(
    "/{job_id}/save",
    summary="Unsave/Unbookmark Job",
    description="Removes a bookmarked job for the authenticated candidate.",
)
def unsave_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Remove bookmark for candidate."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)

    saved_repo = SavedJobRepository(db)
    removed = saved_repo.unsave_job(profile_id=profile.id, job_id=job_id)
    return {"status": "unsaved", "job_id": str(job_id), "removed": removed}
