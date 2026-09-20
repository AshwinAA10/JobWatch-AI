"""Unit tests for MonitoringScheduler lifecycle, configuration, and cycle triggering."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.config import Settings
from app.monitoring.executor import MonitoringExecutor
from app.monitoring.scheduler import MonitoringScheduler, get_scheduler, reset_scheduler


def test_scheduler_disabled_prevents_start():
    """When MONITORING_ENABLED is False, start() must return False and not run."""
    settings = Settings(MONITORING_ENABLED=False)
    scheduler = MonitoringScheduler(settings=settings)

    assert not scheduler.is_enabled
    assert not scheduler.is_running

    started = asyncio.run(scheduler.start())
    assert not started
    assert not scheduler.is_running


def test_scheduler_lifecycle_start_and_stop():
    """Verify scheduler startup, loop execution, and graceful shutdown."""
    settings = Settings(MONITORING_ENABLED=True, MONITORING_INTERVAL_SECONDS=1)
    mock_executor = MagicMock(spec=MonitoringExecutor)
    mock_executor.execute_all_active_sources = AsyncMock(return_value=[])

    scheduler = MonitoringScheduler(executor=mock_executor, settings=settings)

    async def run_test():
        started = await scheduler.start()
        assert started
        assert scheduler.is_running
        assert scheduler.next_run_at is not None

        # Duplicate start call should return False
        dup_started = await scheduler.start()
        assert not dup_started

        # Stop scheduler
        await scheduler.stop()
        assert not scheduler.is_running
        assert scheduler.next_run_at is None

    asyncio.run(run_test())


def test_scheduler_manual_trigger_cycle():
    """Verify manual cycle triggering dispatches active sources and updates last_run_at."""
    settings = Settings(MONITORING_ENABLED=False)
    mock_executor = MagicMock(spec=MonitoringExecutor)
    mock_executor.execute_all_active_sources = AsyncMock(return_value=[])

    scheduler = MonitoringScheduler(executor=mock_executor, settings=settings)

    async def run_trigger():
        assert scheduler.last_run_at is None
        results = await scheduler.trigger_cycle()
        assert results == []
        assert scheduler.last_run_at is not None
        mock_executor.execute_all_active_sources.assert_called_once()

    asyncio.run(run_trigger())


def test_scheduler_singleton_management():
    """Verify get_scheduler and reset_scheduler behavior."""
    reset_scheduler()
    s1 = get_scheduler()
    s2 = get_scheduler()
    assert s1 is s2

    reset_scheduler()
    s3 = get_scheduler()
    assert s3 is not s1
    reset_scheduler()
