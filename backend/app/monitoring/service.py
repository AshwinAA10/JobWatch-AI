"""MonitoringService: orchestrates a single career source monitoring execution."""

import asyncio
import logging
import time
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.connectors.exceptions import (
    ConnectorConfigurationError,
    ConnectorError,
    UnsupportedConnectorError,
)
from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.models.career_source import CareerSource
from app.models.monitoring_run import (
    MonitoringRun,
    MonitoringRunStatus,
    MonitoringTriggerType,
)
from app.monitoring.exceptions import (
    MonitoringError,
    MonitoringExecutionTimeoutError,
    SourceInactiveError,
    SourceNotFoundError,
)
from app.repositories.career_source import CareerSourceRepository
from app.repositories.monitoring_run import MonitoringRunRepository
from app.services.ingestion import IngestionResult, JobIngestionService

logger = logging.getLogger("jobwatch.monitoring.service")


class MonitoringService:
    """Orchestrates monitoring runs for individual career sources.
    
    Coordinates lifecycle transitions, executes the ingestion pipeline,
    manages high-level transient retries, and records execution metrics.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self._external_db = db
        self.settings = settings or get_settings()

    def _get_db(self) -> Session:
        if self._external_db is not None:
            return self._external_db
        return SessionLocal()

    def _close_db_if_local(self, db: Session) -> None:
        if self._external_db is None:
            db.close()

    async def run_source(
        self,
        source_id: UUID,
        trigger_type: str = MonitoringTriggerType.SCHEDULED.value,
    ) -> MonitoringRun:
        """Execute a complete monitoring cycle for a given CareerSource ID.
        
        Args:
            source_id: UUID of the target CareerSource.
            trigger_type: Origin of the execution (SCHEDULED or MANUAL).
            
        Returns:
            The finalized MonitoringRun database record.
            
        Raises:
            SourceNotFoundError: If the source does not exist.
            SourceInactiveError: If the source is marked inactive.
        """
        db = self._get_db()
        try:
            source_repo = CareerSourceRepository(db)
            run_repo = MonitoringRunRepository(db)

            source = source_repo.get_by_id(source_id)
            if source is None:
                raise SourceNotFoundError(
                    f"CareerSource with ID '{source_id}' not found",
                    source_id=source_id,
                )

            if not source.is_active:
                raise SourceInactiveError(
                    f"CareerSource '{source.name}' ({source_id}) is inactive",
                    source_id=source_id,
                )

            # 1. Initialize MonitoringRun in PENDING status
            run = run_repo.create(
                career_source_id=source.id,
                trigger_type=trigger_type,
                status=MonitoringRunStatus.PENDING.value,
                attempt=1,
            )

            # 2. Transition to RUNNING
            run = run_repo.mark_running(run)

            logger.info(
                "Starting monitoring run %s for source '%s' (type=%s, trigger=%s)",
                run.id,
                source.name,
                source.source_type,
                trigger_type,
            )

        finally:
            self._close_db_if_local(db)

        # 3. Execute ingestion with bounded retries and timeout
        return await self._execute_with_retries(source_id, run.id)

    async def _execute_with_retries(
        self,
        source_id: UUID,
        run_id: UUID,
    ) -> MonitoringRun:
        """Run the ingestion pipeline with bounded retries on transient errors."""
        max_attempts = self.settings.MONITORING_MAX_RETRIES + 1
        current_attempt = 0
        last_error: Optional[Exception] = None

        while current_attempt < max_attempts:
            current_attempt += 1

            # Update attempt number in DB
            db = self._get_db()
            try:
                run_repo = MonitoringRunRepository(db)
                run = run_repo.get_by_id(run_id)
                if run:
                    run.attempt = current_attempt
                    db.commit()
            finally:
                self._close_db_if_local(db)

            try:
                logger.debug(
                    "Executing ingestion for source %s (attempt %d/%d)",
                    source_id,
                    current_attempt,
                    max_attempts,
                )

                # Execute ingestion within configured timeout
                result = await asyncio.wait_for(
                    self._execute_ingestion(source_id),
                    timeout=self.settings.MONITORING_SOURCE_TIMEOUT_SECONDS,
                )

                # Execution succeeded (full or partial)
                return self._finalize_success(run_id, result)

            except asyncio.TimeoutError as exc:
                last_error = MonitoringExecutionTimeoutError(
                    f"Monitoring execution timed out after {self.settings.MONITORING_SOURCE_TIMEOUT_SECONDS}s",
                    source_id=source_id,
                )
                logger.warning(
                    "Monitoring timeout on source %s (attempt %d/%d)",
                    source_id,
                    current_attempt,
                    max_attempts,
                )

            except (ConnectorConfigurationError, UnsupportedConnectorError) as exc:
                # Permanent / configuration error - do NOT retry
                logger.error(
                    "Permanent connector configuration error on source %s: %s",
                    source_id,
                    exc,
                )
                return self._finalize_failure(run_id, str(exc), error_count=1)

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Transient monitoring error on source %s (attempt %d/%d): %s",
                    source_id,
                    current_attempt,
                    max_attempts,
                    exc,
                )

            # Check if we should retry
            if current_attempt < max_attempts:
                backoff = self.settings.MONITORING_RETRY_BACKOFF_SECONDS * current_attempt
                logger.info(
                    "Backing off for %.2fs before retrying source %s",
                    backoff,
                    source_id,
                )
                await asyncio.sleep(backoff)

        # All attempts exhausted
        error_msg = str(last_error) if last_error else "Monitoring execution failed"
        return self._finalize_failure(run_id, error_msg, error_count=current_attempt)

    async def _execute_ingestion(self, source_id: UUID) -> IngestionResult:
        """Call JobIngestionService in an isolated database session."""
        db = self._get_db()
        try:
            ingestion_service = JobIngestionService(db)
            return await ingestion_service.ingest_source(source_id)
        finally:
            self._close_db_if_local(db)

    def _finalize_success(self, run_id: UUID, result: IngestionResult) -> MonitoringRun:
        """Record successful or partially successful monitoring run."""
        db = self._get_db()
        try:
            run_repo = MonitoringRunRepository(db)
            run = run_repo.get_by_id(run_id)
            if not run:
                raise MonitoringError(f"MonitoringRun '{run_id}' not found during finalization")

            # Determine SUCCESS vs PARTIAL_SUCCESS
            if result.jobs_skipped > 0 or result.errors:
                status = MonitoringRunStatus.PARTIAL_SUCCESS.value
            else:
                status = MonitoringRunStatus.SUCCESS.value

            error_summary = "; ".join(result.errors[:5]) if result.errors else None

            final_run = run_repo.complete_run(
                run=run,
                status=status,
                jobs_fetched=result.jobs_fetched,
                jobs_created=result.jobs_persisted,
                jobs_updated=result.jobs_updated,
                jobs_skipped=result.jobs_skipped,
                error_count=len(result.errors),
                error_message=error_summary,
            )
            logger.info(
                "Monitoring run %s finalized with status %s (%d fetched, %d created, %d updated, %d skipped)",
                run_id,
                status,
                result.jobs_fetched,
                result.jobs_persisted,
                result.jobs_updated,
                result.jobs_skipped,
            )
            return final_run
        finally:
            self._close_db_if_local(db)

    def _finalize_failure(
        self,
        run_id: UUID,
        error_message: str,
        error_count: int = 1,
    ) -> MonitoringRun:
        """Record failed monitoring run."""
        db = self._get_db()
        try:
            run_repo = MonitoringRunRepository(db)
            run = run_repo.get_by_id(run_id)
            if not run:
                raise MonitoringError(f"MonitoringRun '{run_id}' not found during failure finalization")

            final_run = run_repo.mark_failed(
                run=run,
                error_message=error_message,
                error_count=error_count,
            )
            logger.error("Monitoring run %s marked FAILED: %s", run_id, error_message)
            return final_run
        finally:
            self._close_db_if_local(db)
