"""Application tracking business logic and lifecycle service."""

import math
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_history import ApplicationHistory
from app.models.application_note import ApplicationNote
from app.models.enums import ApplicationStatus
from app.models.interview import Interview
from app.repositories.application import ApplicationRepository
from app.repositories.application_history import ApplicationHistoryRepository
from app.repositories.application_note import ApplicationNoteRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.job_match import JobMatchRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationListItem,
    ApplicationStatistics,
    ApplicationUpdate,
    InterviewCreate,
    InterviewUpdate,
)
from app.services.exceptions import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    InvalidStatusTransitionError,
    InterviewNotFoundError,
    JobNotFoundError,
    ResourceNotFoundError,
)

# Defined lifecycle transitions with candidate correction support
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    ApplicationStatus.APPLIED.value: {
        ApplicationStatus.SCREENING.value,
        ApplicationStatus.INTERVIEW.value,
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.SCREENING.value: {
        ApplicationStatus.INTERVIEW.value,
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
        ApplicationStatus.APPLIED.value,
    },
    ApplicationStatus.INTERVIEW.value: {
        ApplicationStatus.OFFER.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
        ApplicationStatus.SCREENING.value,
        ApplicationStatus.APPLIED.value,
    },
    ApplicationStatus.OFFER.value: {
        ApplicationStatus.ACCEPTED.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.WITHDRAWN.value,
        ApplicationStatus.INTERVIEW.value,
    },
    ApplicationStatus.REJECTED.value: {
        ApplicationStatus.APPLIED.value,
        ApplicationStatus.SCREENING.value,
        ApplicationStatus.INTERVIEW.value,
        ApplicationStatus.OFFER.value,
    },
    ApplicationStatus.WITHDRAWN.value: {
        ApplicationStatus.APPLIED.value,
        ApplicationStatus.SCREENING.value,
        ApplicationStatus.INTERVIEW.value,
    },
    ApplicationStatus.ACCEPTED.value: {
        ApplicationStatus.OFFER.value,
        ApplicationStatus.WITHDRAWN.value,
    },
}


class ApplicationService:
    """Service orchestrating candidate application tracking, notes, interviews, and lifecycle."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.app_repo = ApplicationRepository(db)
        self.history_repo = ApplicationHistoryRepository(db)
        self.note_repo = ApplicationNoteRepository(db)
        self.interview_repo = InterviewRepository(db)
        self.job_repo = JobRepository(db)
        self.match_repo = JobMatchRepository(db)

    def create_application(
        self,
        profile_id: UUID,
        payload: ApplicationCreate,
    ) -> Application:
        """Create a new tracked application with initial audit history."""
        job_id = payload.job_id
        company_name = payload.company_name
        job_title = payload.job_title
        job_location = payload.job_location
        external_app_url = payload.external_application_url
        match_score: Optional[float] = None

        if job_id:
            # Check duplicate application for this job
            existing = self.app_repo.get_by_profile_and_job(profile_id, job_id)
            if existing:
                raise DuplicateApplicationError(
                    f"You have already created an application for job '{existing.job_title}' at {existing.company_name}."
                )

            # Retrieve canonical job context
            job = self.job_repo.get_by_id_with_relations(job_id)
            if not job:
                raise JobNotFoundError(job_id)

            company_name = company_name or (job.company.name if job.company else "Unknown Company")
            job_title = job_title or job.title
            job_location = job_location or job.location
            external_app_url = external_app_url or job.application_url

            # Snapshot match score if available
            existing_match = self.match_repo.get_by_profile_and_job(profile_id, job.id)
            if existing_match:
                match_score = existing_match.score

        if not company_name or not company_name.strip():
            raise ValueError("Company name is required to track an application.")
        if not job_title or not job_title.strip():
            raise ValueError("Job title is required to track an application.")

        return self.app_repo.create(
            profile_id=profile_id,
            job_id=job_id,
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            status=ApplicationStatus.APPLIED.value,
            job_location=job_location.strip() if job_location else None,
            external_application_url=external_app_url.strip() if external_app_url else None,
            match_score_at_application=match_score,
            notes=payload.notes.strip() if payload.notes else None,
            applied_at=payload.applied_at,
        )

    def get_application_for_candidate(
        self,
        profile_id: UUID,
        application_id: UUID,
    ) -> Application:
        """Retrieve application ensuring candidate profile ownership."""
        app = self.app_repo.get_by_id_and_profile(application_id, profile_id)
        if not app:
            raise ApplicationNotFoundError(application_id)
        return app

    def list_applications_for_candidate(
        self,
        profile_id: UUID,
        status: Optional[str] = None,
        company: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ApplicationListItem], int, int]:
        """List paginated applications for candidate with filter and search."""
        skip = (page - 1) * page_size
        items, total = self.app_repo.list_for_profile(
            profile_id=profile_id,
            status=status,
            company=company,
            search=search,
            sort_by=sort_by,
            skip=skip,
            limit=page_size,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        list_items = [
            ApplicationListItem(
                id=item.id,
                profile_id=item.profile_id,
                job_id=item.job_id,
                status=item.status,
                applied_at=item.applied_at,
                last_status_changed_at=item.last_status_changed_at,
                company_name=item.company_name,
                job_title=item.job_title,
                job_location=item.job_location,
                external_application_url=item.external_application_url,
                match_score_at_application=item.match_score_at_application,
                notes_count=len(item.application_notes),
                interviews_count=len(item.interviews),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ]

        return list_items, total, total_pages

    def update_application_status(
        self,
        profile_id: UUID,
        application_id: UUID,
        new_status: ApplicationStatus,
        note: Optional[str] = None,
    ) -> Application:
        """Validate status transition and transition application atomically."""
        app = self.get_application_for_candidate(profile_id, application_id)
        current_status = app.status
        target_status = new_status.value

        if current_status == target_status:
            raise InvalidStatusTransitionError(f"Application is already in status '{target_status}'.")

        allowed = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Cannot transition application from '{current_status}' to '{target_status}'."
            )

        return self.app_repo.update_status(
            application=app,
            new_status=target_status,
            note=note.strip() if note else None,
        )

    def update_application_details(
        self,
        profile_id: UUID,
        application_id: UUID,
        payload: ApplicationUpdate,
    ) -> Application:
        """Update mutable fields on an existing application."""
        app = self.get_application_for_candidate(profile_id, application_id)
        update_dict = payload.model_dump(exclude_unset=True)
        return self.app_repo.update_application(app, **update_dict)

    def delete_application(
        self,
        profile_id: UUID,
        application_id: UUID,
    ) -> None:
        """Delete application along with child notes, interviews, and history."""
        app = self.get_application_for_candidate(profile_id, application_id)
        self.app_repo.delete(app)

    def get_statistics(self, profile_id: UUID) -> ApplicationStatistics:
        """Aggregate application lifecycle counts for candidate dashboard."""
        counts = self.app_repo.get_counts_by_status(profile_id)
        return ApplicationStatistics(
            total=counts.get("TOTAL", 0),
            applied=counts.get("APPLIED", 0),
            screening=counts.get("SCREENING", 0),
            interview=counts.get("INTERVIEW", 0),
            offer=counts.get("OFFER", 0),
            rejected=counts.get("REJECTED", 0),
            withdrawn=counts.get("WITHDRAWN", 0),
            accepted=counts.get("ACCEPTED", 0),
        )

    # --- Notes Management ---

    def add_note(
        self,
        profile_id: UUID,
        application_id: UUID,
        content: str,
    ) -> ApplicationNote:
        """Add candidate note to an owned application."""
        app = self.get_application_for_candidate(profile_id, application_id)
        return self.note_repo.create(application_id=app.id, content=content.strip())

    def get_notes(
        self,
        profile_id: UUID,
        application_id: UUID,
    ) -> List[ApplicationNote]:
        """Fetch all notes for an owned application."""
        app = self.get_application_for_candidate(profile_id, application_id)
        return self.note_repo.list_for_application(app.id)

    def update_note(
        self,
        profile_id: UUID,
        application_id: UUID,
        note_id: UUID,
        content: str,
    ) -> ApplicationNote:
        """Edit an existing candidate note."""
        app = self.get_application_for_candidate(profile_id, application_id)
        note = self.note_repo.get_by_id(note_id)
        if not note or note.application_id != app.id:
            raise ResourceNotFoundError(f"Note {note_id} not found on application {application_id}")
        return self.note_repo.update(note, content.strip())

    def delete_note(
        self,
        profile_id: UUID,
        application_id: UUID,
        note_id: UUID,
    ) -> None:
        """Delete an existing candidate note."""
        app = self.get_application_for_candidate(profile_id, application_id)
        note = self.note_repo.get_by_id(note_id)
        if not note or note.application_id != app.id:
            raise ResourceNotFoundError(f"Note {note_id} not found on application {application_id}")
        self.note_repo.delete(note)

    # --- Interviews Management ---

    def create_interview(
        self,
        profile_id: UUID,
        application_id: UUID,
        payload: InterviewCreate,
    ) -> Interview:
        """Schedule a new interview round on an owned application."""
        app = self.get_application_for_candidate(profile_id, application_id)
        return self.interview_repo.create(
            application_id=app.id,
            interview_type=payload.interview_type.value,
            status=payload.status.value,
            scheduled_at=payload.scheduled_at,
            duration_minutes=payload.duration_minutes,
            interviewer_names=payload.interviewer_names.strip() if payload.interviewer_names else None,
            location=payload.location.strip() if payload.location else None,
            meeting_url=payload.meeting_url.strip() if payload.meeting_url else None,
            notes=payload.notes.strip() if payload.notes else None,
        )

    def get_interviews(
        self,
        profile_id: UUID,
        application_id: UUID,
    ) -> List[Interview]:
        """Fetch all interviews for an owned application."""
        app = self.get_application_for_candidate(profile_id, application_id)
        return self.interview_repo.list_for_application(app.id)

    def update_interview(
        self,
        profile_id: UUID,
        application_id: UUID,
        interview_id: UUID,
        payload: InterviewUpdate,
    ) -> Interview:
        """Update details or status of an interview round."""
        app = self.get_application_for_candidate(profile_id, application_id)
        interview = self.interview_repo.get_by_id(interview_id)
        if not interview or interview.application_id != app.id:
            raise InterviewNotFoundError(interview_id)

        update_dict = payload.model_dump(exclude_unset=True)
        # Convert enums to string values
        if "interview_type" in update_dict and update_dict["interview_type"]:
            update_dict["interview_type"] = update_dict["interview_type"].value
        if "status" in update_dict and update_dict["status"]:
            update_dict["status"] = update_dict["status"].value

        return self.interview_repo.update(interview, **update_dict)

    def delete_interview(
        self,
        profile_id: UUID,
        application_id: UUID,
        interview_id: UUID,
    ) -> None:
        """Delete an interview round."""
        app = self.get_application_for_candidate(profile_id, application_id)
        interview = self.interview_repo.get_by_id(interview_id)
        if not interview or interview.application_id != app.id:
            raise InterviewNotFoundError(interview_id)
        self.interview_repo.delete(interview)
