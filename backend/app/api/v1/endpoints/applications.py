"""API endpoints for candidate job application tracking and lifecycle."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import ApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationHistoryResponse,
    ApplicationListResponse,
    ApplicationNoteCreate,
    ApplicationNoteResponse,
    ApplicationNoteUpdate,
    ApplicationResponse,
    ApplicationStatistics,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    InterviewCreate,
    InterviewResponse,
    InterviewUpdate,
)
from app.services.application import ApplicationService
from app.services.exceptions import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    InvalidStatusTransitionError,
    InterviewNotFoundError,
    JobNotFoundError,
    ResourceNotFoundError,
)
from app.services.profile import ProfileService

router = APIRouter()


def _get_candidate_profile_id(current_user: User, db: Session) -> UUID:
    """Helper to ensure and retrieve candidate profile ID for authenticated user."""
    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(current_user.id)
    return profile.id


# --- Application Core Endpoints ---

@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Track a New Job Application",
    description="Records a new job application submitted by the candidate.",
)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Create a new tracked application."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        app = service.create_application(profile_id, payload)
        return ApplicationResponse.model_validate(app)
    except DuplicateApplicationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/stats",
    response_model=ApplicationStatistics,
    summary="Get Application Lifecycle Statistics",
    description="Aggregates total application counts by status for dashboard metrics.",
)
def get_application_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationStatistics:
    """Retrieve application summary metrics."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    return service.get_statistics(profile_id)


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List Tracked Applications",
    description="Retrieves candidate's applications with filtering, search, sorting, and pagination.",
)
def list_applications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. APPLIED, INTERVIEW)"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    q: Optional[str] = Query(None, description="Free-text search on title, company, location"),
    search: Optional[str] = Query(None, description="Alias for q"),
    sort_by: str = Query("newest", pattern="^(newest|oldest|recently_updated|company)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    """List paginated applications for candidate."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    query_search = q or search
    items, total, total_pages = service.list_applications_for_candidate(
        profile_id=profile_id,
        status=status_filter,
        company=company,
        search=query_search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return ApplicationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get Application Details",
    description="Fetches full details of an application including history, notes, and interviews.",
)
def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Retrieve application by ID."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        app = service.get_application_for_candidate(profile_id, application_id)
        return ApplicationResponse.model_validate(app)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Update Application Details",
    description="Edits mutable metadata on an existing application.",
)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Update application fields."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        app = service.update_application_details(profile_id, application_id, payload)
        return ApplicationResponse.model_validate(app)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Tracked Application",
    description="Permanently deletes an application and its child records.",
)
def delete_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete an application."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        service.delete_application(profile_id, application_id)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update Application Status",
    description="Transitions lifecycle status and records audit history event atomically.",
)
def update_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Transition application status."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        app = service.update_application_status(
            profile_id=profile_id,
            application_id=application_id,
            new_status=payload.status,
            note=payload.note,
        )
        return ApplicationResponse.model_validate(app)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{application_id}/history",
    response_model=List[ApplicationHistoryResponse],
    summary="Get Status Transition History",
    description="Retrieves chronological timeline of status transitions for an application.",
)
def get_application_history(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ApplicationHistoryResponse]:
    """List status history entries."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        app = service.get_application_for_candidate(profile_id, application_id)
        history = service.history_repo.list_for_application(app.id)
        return [ApplicationHistoryResponse.model_validate(h) for h in history]
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# --- Notes Endpoints ---

@router.get(
    "/{application_id}/notes",
    response_model=List[ApplicationNoteResponse],
    summary="List Application Notes",
    description="Fetches candidate notes attached to the application.",
)
def list_application_notes(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ApplicationNoteResponse]:
    """Retrieve notes for application."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        notes = service.get_notes(profile_id, application_id)
        return [ApplicationNoteResponse.model_validate(n) for n in notes]
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{application_id}/notes",
    response_model=ApplicationNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Note to Application",
    description="Creates a new private candidate note on the application.",
)
def add_application_note(
    application_id: UUID,
    payload: ApplicationNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationNoteResponse:
    """Create a new candidate note."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        note = service.add_note(profile_id, application_id, payload.content)
        return ApplicationNoteResponse.model_validate(note)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{application_id}/notes/{note_id}",
    response_model=ApplicationNoteResponse,
    summary="Edit Application Note",
    description="Updates the content of an existing note.",
)
def update_application_note(
    application_id: UUID,
    note_id: UUID,
    payload: ApplicationNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationNoteResponse:
    """Edit candidate note."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        note = service.update_note(profile_id, application_id, note_id, payload.content)
        return ApplicationNoteResponse.model_validate(note)
    except (ApplicationNotFoundError, ResourceNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{application_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Application Note",
    description="Permanently deletes a candidate note.",
)
def delete_application_note(
    application_id: UUID,
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete candidate note."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        service.delete_note(profile_id, application_id, note_id)
    except (ApplicationNotFoundError, ResourceNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# --- Interviews Endpoints ---

@router.get(
    "/{application_id}/interviews",
    response_model=List[InterviewResponse],
    summary="List Scheduled Interviews",
    description="Retrieves scheduled and completed interviews for an application.",
)
def list_interviews(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[InterviewResponse]:
    """Retrieve interviews for application."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        interviews = service.get_interviews(profile_id, application_id)
        return [InterviewResponse.model_validate(i) for i in interviews]
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{application_id}/interviews",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule an Interview",
    description="Adds an interview round to the application.",
)
def create_interview(
    application_id: UUID,
    payload: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    """Schedule interview."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        interview = service.create_interview(profile_id, application_id, payload)
        return InterviewResponse.model_validate(interview)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/{application_id}/interviews/{interview_id}",
    response_model=InterviewResponse,
    summary="Update Interview Details or Status",
    description="Edits details or status (e.g. COMPLETED, CANCELLED) of an interview.",
)
def update_interview(
    application_id: UUID,
    interview_id: UUID,
    payload: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    """Edit interview."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        interview = service.update_interview(profile_id, application_id, interview_id, payload)
        return InterviewResponse.model_validate(interview)
    except (ApplicationNotFoundError, InterviewNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/{application_id}/interviews/{interview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Interview Record",
    description="Permanently deletes an interview record.",
)
def delete_interview(
    application_id: UUID,
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete interview."""
    profile_id = _get_candidate_profile_id(current_user, db)
    service = ApplicationService(db)
    try:
        service.delete_interview(profile_id, application_id, interview_id)
    except (ApplicationNotFoundError, InterviewNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
