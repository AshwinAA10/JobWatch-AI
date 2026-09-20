"""MonitoringExecutor: manages concurrency, same-source locking, and error isolation."""

import asyncio
import logging
from typing import List, Optional, Set, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.models.monitoring_run import MonitoringRun, MonitoringTriggerType
from app.monitoring.exceptions import (
    MonitoringError,
    SourceAlreadyRunningError,
    SourceInactiveError,
    SourceNotFoundError,
)
from app.monitoring.service import MonitoringService
from app.repositories.career_source import CareerSourceRepository
from app.repositories.monitoring_run import MonitoringRunRepository

logger = logging.getLogger("jobwatch.monitoring.executor")


class MonitoringExecutor:
    """Executes monitoring runs with bounded concurrency, overlap protection, and error isolation."""

    def __init__(
        self,
        service: Optional[MonitoringService] = None,
        db: Optional[Session] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.service = service or MonitoringService(db=db, settings=self.settings)
        self._external_db = db
        self._active_sources: Set[UUID] = set()
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(self.settings.MONITORING_MAX_CONCURRENCY)

    def _get_db(self) -> Session:
        if self._external_db is not None:
            return self._external_db
        return SessionLocal()

    def _close_db_if_local(self, db: Session) -> None:
        if self._external_db is None:
            db.close()

    def get_active_sources_count(self) -> int:
        """Return the number of sources currently being monitored."""
        return len(self._active_sources)

    async def execute_source(
        self,
        source_id: UUID,
        trigger_type: str = MonitoringTriggerType.SCHEDULED.value,
    ) -> Tuple[Optional[MonitoringRun], str]:
        """Execute a monitoring run for a specific source, ensuring single-source overlap protection.
        
        Returns:
            Tuple of (MonitoringRun, message) on success, or (None, reason) if skipped/blocked.
        """
        # 1. Enforce same-source overlap lock in-memory
        async with self._lock:
            if source_id in self._active_sources:
                msg = f"Source {source_id} is already actively running. Skipping duplicate execution."
                logger.warning(msg)
                return None, msg

            # Also verify against DB for existing active runs and source active state
            db = self._get_db()
            try:
                run_repo = MonitoringRunRepository(db)
                active_db_run = run_repo.get_active_run_for_source(source_id)
                if active_db_run:
                    msg = f"Source {source_id} has existing active run {active_db_run.id}. Skipping duplicate execution."
                    logger.warning(msg)
                    return None, msg

                source_repo = CareerSourceRepository(db)
                source = source_repo.get_by_id(source_id)
                if source is None:
                    msg = f"CareerSource with ID '{source_id}' not found"
                    logger.warning(msg)
                    return None, msg
                if not source.is_active:
                    msg = f"CareerSource '{source.name}' ({source_id}) is inactive"
                    logger.info(msg)
                    return None, msg
            finally:
                self._close_db_if_local(db)

            self._active_sources.add(source_id)

        try:
            # 2. Acquire concurrency semaphore
            async with self._semaphore:
                logger.debug("Acquired execution slot for source %s", source_id)
                run = await self.service.run_source(source_id, trigger_type=trigger_type)
                return run, f"Execution completed with status {run.status}"

        except SourceNotFoundError as exc:
            logger.error("Failed to execute source %s: %s", source_id, exc)
            return None, str(exc)

        except SourceInactiveError as exc:
            logger.info("Skipped inactive source %s: %s", source_id, exc)
            return None, str(exc)

        except Exception as exc:
            logger.exception("Unexpected error executing source %s: %s", source_id, exc)
            return None, f"Execution failed: {exc}"

        finally:
            async with self._lock:
                self._active_sources.discard(source_id)

    async def execute_all_active_sources(
        self,
        trigger_type: str = MonitoringTriggerType.SCHEDULED.value,
    ) -> List[Tuple[UUID, Optional[MonitoringRun], str]]:
        """Find and execute all active career sources concurrently with isolated error handling.
        
        Returns:
            List of (source_id, MonitoringRun, message) for each active source.
        """
        db = self._get_db()
        try:
            source_repo = CareerSourceRepository(db)
            # Find all active sources
            # Query active sources across companies
            from app.models.career_source import CareerSource
            from sqlalchemy import select
            stmt = select(CareerSource).where(CareerSource.is_active.is_(True))
            active_sources = list(db.scalars(stmt).all())
            source_ids = [s.id for s in active_sources]
        finally:
            self._close_db_if_local(db)

        if not source_ids:
            logger.info("No active career sources found to monitor.")
            return []

        logger.info(
            "Dispatching monitoring cycle for %d active sources (max concurrency: %d)",
            len(source_ids),
            self.settings.MONITORING_MAX_CONCURRENCY,
        )

        # Dispatch all sources with isolated execution
        tasks = [
            self._execute_source_wrapper(source_id, trigger_type)
            for source_id in source_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def _execute_source_wrapper(
        self,
        source_id: UUID,
        trigger_type: str,
    ) -> Tuple[UUID, Optional[MonitoringRun], str]:
        """Wrapper to capture source ID alongside execution results."""
        run, msg = await self.execute_source(source_id, trigger_type)
        return source_id, run, msg
