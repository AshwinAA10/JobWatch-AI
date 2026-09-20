"""MonitoringScheduler: asynchronous in-process periodic scheduler."""

import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from app.core.config import Settings, get_settings
from app.models.monitoring_run import MonitoringRun, MonitoringTriggerType
from app.monitoring.executor import MonitoringExecutor

logger = logging.getLogger("jobwatch.monitoring.scheduler")


class MonitoringScheduler:
    """Asynchronous in-process scheduler that triggers periodic monitoring cycles."""

    def __init__(
        self,
        executor: Optional[MonitoringExecutor] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.executor = executor or MonitoringExecutor(settings=self.settings)
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._is_running = False
        self._last_run_at: Optional[datetime] = None
        self._next_run_at: Optional[datetime] = None

    @property
    def is_enabled(self) -> bool:
        """Whether monitoring is globally enabled in settings."""
        return self.settings.MONITORING_ENABLED

    @property
    def is_running(self) -> bool:
        """Whether the scheduler task loop is currently active."""
        return self._is_running and self._task is not None and not self._task.done()

    @property
    def interval_seconds(self) -> int:
        """Scheduled cycle interval in seconds."""
        return self.settings.MONITORING_INTERVAL_SECONDS

    @property
    def last_run_at(self) -> Optional[datetime]:
        """Timestamp of the most recently initiated scheduled run."""
        return self._last_run_at

    @property
    def next_run_at(self) -> Optional[datetime]:
        """Timestamp when the next scheduled cycle will execute."""
        return self._next_run_at

    async def start(self) -> bool:
        """Start the background monitoring loop if enabled.
        
        Returns:
            True if started, False if disabled or already running.
        """
        if not self.is_enabled:
            logger.info("MonitoringScheduler is disabled by configuration (MONITORING_ENABLED=False).")
            return False

        if self.is_running:
            logger.warning("MonitoringScheduler is already running. Ignoring duplicate start call.")
            return False

        self._stop_event.clear()
        self._is_running = True
        self._next_run_at = datetime.now(timezone.utc) + timedelta(seconds=self.interval_seconds)
        self._task = asyncio.create_task(self._run_loop(), name="jobwatch-monitoring-scheduler")
        logger.info(
            "MonitoringScheduler started (interval: %ds, max concurrency: %d)",
            self.interval_seconds,
            self.settings.MONITORING_MAX_CONCURRENCY,
        )
        return True

    async def stop(self, timeout: float = 10.0) -> None:
        """Gracefully stop the background monitoring loop."""
        if not self._is_running:
            return

        logger.info("Stopping MonitoringScheduler...")
        self._is_running = False
        self._stop_event.set()
        self._next_run_at = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logger.debug("Scheduler task cancelled during shutdown")
            except Exception as exc:
                logger.error("Error stopping scheduler task: %s", exc)

        self._task = None
        logger.info("MonitoringScheduler stopped.")

    async def trigger_cycle(
        self,
        trigger_type: str = MonitoringTriggerType.MANUAL.value,
    ) -> List[Tuple[UUID, Optional[MonitoringRun], str]]:
        """Trigger an immediate monitoring cycle across all active sources."""
        logger.info("Triggering monitoring cycle (trigger_type=%s)", trigger_type)
        self._last_run_at = datetime.now(timezone.utc)
        return await self.executor.execute_all_active_sources(trigger_type=trigger_type)

    async def _run_loop(self) -> None:
        """Internal background loop running at configured intervals."""
        # Calculate first next_run_at
        self._next_run_at = datetime.now(timezone.utc) + timedelta(seconds=self.interval_seconds)

        while not self._stop_event.is_set():
            try:
                # Wait for next interval or stop event
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=float(self.interval_seconds),
                    )
                    # If stop_event was triggered, exit loop
                    break
                except asyncio.TimeoutError:
                    # Interval elapsed - proceed with monitoring cycle
                    pass

                if self._stop_event.is_set():
                    break

                self._last_run_at = datetime.now(timezone.utc)
                self._next_run_at = self._last_run_at + timedelta(seconds=self.interval_seconds)

                logger.info("Executing scheduled monitoring cycle...")
                await self.executor.execute_all_active_sources(
                    trigger_type=MonitoringTriggerType.SCHEDULED.value,
                )

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Unexpected error in monitoring scheduler loop: %s", exc)
                # Continue running subsequent intervals even if one cycle had an uncaught exception
                await asyncio.sleep(5.0)


# Global singleton instance for application lifespan
_global_scheduler: Optional[MonitoringScheduler] = None


def get_scheduler() -> MonitoringScheduler:
    """Return the application-wide singleton MonitoringScheduler instance."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = MonitoringScheduler()
    return _global_scheduler


def reset_scheduler() -> None:
    """Reset the application-wide singleton (useful in tests)."""
    global _global_scheduler
    _global_scheduler = None
