"""Repository for MonitoringRun data access operations."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.monitoring_run import (
    MonitoringRun,
    MonitoringRunStatus,
    MonitoringTriggerType,
)


class MonitoringRunRepository:
    """Data access repository for MonitoringRun entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        career_source_id: UUID,
        trigger_type: str = MonitoringTriggerType.SCHEDULED.value,
        status: str = MonitoringRunStatus.PENDING.value,
        attempt: int = 1,
    ) -> MonitoringRun:
        """Create and persist a new MonitoringRun record."""
        run = MonitoringRun(
            career_source_id=career_source_id,
            status=status,
            trigger_type=trigger_type,
            attempt=attempt,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: UUID) -> Optional[MonitoringRun]:
        """Fetch a single MonitoringRun by ID."""
        return self.db.get(MonitoringRun, run_id)

    def mark_running(self, run: MonitoringRun) -> MonitoringRun:
        """Transition a run into RUNNING status and timestamp its start."""
        run.status = MonitoringRunStatus.RUNNING.value
        run.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return run

    def complete_run(
        self,
        run: MonitoringRun,
        status: str,
        jobs_fetched: int = 0,
        jobs_created: int = 0,
        jobs_updated: int = 0,
        jobs_skipped: int = 0,
        error_count: int = 0,
        error_message: Optional[str] = None,
    ) -> MonitoringRun:
        """Finalize a monitoring run with counts, final status, and completion timestamp."""
        run.status = status
        run.jobs_fetched = jobs_fetched
        run.jobs_created = jobs_created
        run.jobs_updated = jobs_updated
        run.jobs_skipped = jobs_skipped
        run.error_count = error_count
        run.error_message = error_message
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return run

    def mark_failed(
        self,
        run: MonitoringRun,
        error_message: str,
        error_count: int = 1,
    ) -> MonitoringRun:
        """Mark a run as FAILED with an error message."""
        run.status = MonitoringRunStatus.FAILED.value
        run.error_message = error_message
        run.error_count = error_count
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return run

    def mark_cancelled(
        self,
        run: MonitoringRun,
        reason: str = "Execution cancelled",
    ) -> MonitoringRun:
        """Mark an in-progress or pending run as CANCELLED."""
        run.status = MonitoringRunStatus.CANCELLED.value
        run.error_message = reason
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_active_run_for_source(self, career_source_id: UUID) -> Optional[MonitoringRun]:
        """Return currently active (PENDING or RUNNING) run for a career source if one exists."""
        stmt = (
            select(MonitoringRun)
            .where(
                MonitoringRun.career_source_id == career_source_id,
                MonitoringRun.status.in_([
                    MonitoringRunStatus.PENDING.value,
                    MonitoringRunStatus.RUNNING.value,
                ]),
            )
            .order_by(MonitoringRun.created_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def list_runs(
        self,
        career_source_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MonitoringRun]:
        """List monitoring runs with optional filtering and pagination."""
        stmt = select(MonitoringRun)
        if career_source_id is not None:
            stmt = stmt.where(MonitoringRun.career_source_id == career_source_id)
        if status is not None:
            stmt = stmt.where(MonitoringRun.status == status)

        stmt = stmt.order_by(MonitoringRun.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def list_stale_runs(self, threshold_seconds: int = 3600) -> List[MonitoringRun]:
        """Find runs that have been RUNNING longer than the given threshold."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)
        stmt = select(MonitoringRun).where(
            MonitoringRun.status == MonitoringRunStatus.RUNNING.value,
            MonitoringRun.started_at < cutoff,
        )
        return list(self.db.scalars(stmt).all())
