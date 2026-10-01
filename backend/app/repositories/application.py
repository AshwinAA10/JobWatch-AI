"""Repository for Application persistence and query operations."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.application_history import ApplicationHistory


class ApplicationRepository:
    """Data access repository for Application entity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        profile_id: UUID,
        job_id: Optional[UUID],
        company_name: str,
        job_title: str,
        status: str,
        job_location: Optional[str] = None,
        external_application_url: Optional[str] = None,
        match_score_at_application: Optional[float] = None,
        notes: Optional[str] = None,
        applied_at: Optional[datetime] = None,
    ) -> Application:
        """Create and persist a new Application record with initial history."""
        now = datetime.now(timezone.utc)
        app_applied_at = applied_at or now

        app = Application(
            profile_id=profile_id,
            job_id=job_id,
            status=status,
            applied_at=app_applied_at,
            last_status_changed_at=now,
            company_name=company_name,
            job_title=job_title,
            job_location=job_location,
            external_application_url=external_application_url,
            match_score_at_application=match_score_at_application,
            notes=notes,
        )
        self.db.add(app)
        self.db.flush()

        # Add initial history event atomically
        history_entry = ApplicationHistory(
            application_id=app.id,
            old_status=None,
            new_status=status,
            changed_at=now,
            note=notes or "Application marked as submitted",
        )
        self.db.add(history_entry)
        self.db.commit()
        self.db.refresh(app)
        return app

    def get_by_id(self, application_id: UUID) -> Optional[Application]:
        """Fetch application by primary key with relations loaded."""
        stmt = (
            select(Application)
            .options(
                selectinload(Application.history),
                selectinload(Application.application_notes),
                selectinload(Application.interviews),
                selectinload(Application.job),
            )
            .where(Application.id == application_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_id_and_profile(self, application_id: UUID, profile_id: UUID) -> Optional[Application]:
        """Fetch application ensuring candidate ownership."""
        stmt = (
            select(Application)
            .options(
                selectinload(Application.history),
                selectinload(Application.application_notes),
                selectinload(Application.interviews),
                selectinload(Application.job),
            )
            .where(
                Application.id == application_id,
                Application.profile_id == profile_id,
            )
        )
        return self.db.scalars(stmt).first()

    def get_by_profile_and_job(self, profile_id: UUID, job_id: UUID) -> Optional[Application]:
        """Fetch existing application for a candidate profile and specific job."""
        stmt = select(Application).where(
            Application.profile_id == profile_id,
            Application.job_id == job_id,
        )
        return self.db.scalars(stmt).first()

    def list_for_profile(
        self,
        profile_id: UUID,
        status: Optional[str] = None,
        company: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Application], int]:
        """Retrieve paginated applications for candidate profile with filters and sorting."""
        stmt = (
            select(Application)
            .options(
                selectinload(Application.history),
                selectinload(Application.application_notes),
                selectinload(Application.interviews),
                selectinload(Application.job),
            )
            .where(Application.profile_id == profile_id)
        )

        if status:
            stmt = stmt.where(Application.status == status)

        if company:
            stmt = stmt.where(Application.company_name.ilike(f"%{company}%"))

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Application.job_title.ilike(search_pattern),
                    Application.company_name.ilike(search_pattern),
                    Application.job_location.ilike(search_pattern),
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Sorting
        if sort_by == "oldest":
            stmt = stmt.order_by(Application.applied_at.asc())
        elif sort_by == "recently_updated":
            stmt = stmt.order_by(Application.last_status_changed_at.desc())
        elif sort_by == "company":
            stmt = stmt.order_by(Application.company_name.asc())
        else:  # newest / default
            stmt = stmt.order_by(Application.applied_at.desc(), Application.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)
        items = list(self.db.scalars(stmt).all())
        return items, total

    def update_status(
        self,
        application: Application,
        new_status: str,
        note: Optional[str] = None,
    ) -> Application:
        """Atomically transition status and insert audit history entry."""
        now = datetime.now(timezone.utc)
        old_status = application.status

        application.status = new_status
        application.last_status_changed_at = now

        history_entry = ApplicationHistory(
            application_id=application.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=now,
            note=note,
        )
        self.db.add(history_entry)
        self.db.commit()
        self.db.refresh(application)
        return application

    def update_application(
        self,
        application: Application,
        **kwargs,
    ) -> Application:
        """Update mutable fields on an Application instance."""
        for field, value in kwargs.items():
            if hasattr(application, field) and value is not None:
                setattr(application, field, value)

        self.db.commit()
        self.db.refresh(application)
        return application

    def delete(self, application: Application) -> None:
        """Delete an Application record along with cascaded children."""
        self.db.delete(application)
        self.db.commit()

    def get_counts_by_status(self, profile_id: UUID) -> Dict[str, int]:
        """Aggregate total application count and breakdown by status for candidate profile."""
        stmt = (
            select(Application.status, func.count(Application.id))
            .where(Application.profile_id == profile_id)
            .group_by(Application.status)
        )
        rows = self.db.execute(stmt).all()

        counts = {status: 0 for status in [
            "APPLIED", "SCREENING", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN", "ACCEPTED"
        ]}
        total = 0
        for status, count in rows:
            counts[status] = count
            total += count

        counts["TOTAL"] = total
        return counts
