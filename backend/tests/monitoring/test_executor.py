"""Unit tests for MonitoringExecutor concurrency control, same-source locking, and error isolation."""

import asyncio
import uuid
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.monitoring_run import MonitoringRun, MonitoringRunStatus, MonitoringTriggerType
from app.monitoring.executor import MonitoringExecutor
from app.monitoring.service import MonitoringService
from app.services.ingestion import IngestionResult


def create_multiple_sources(db: Session, count: int, is_active: bool = True) -> List[CareerSource]:
    """Create multiple active CareerSource records for concurrency tests."""
    company = Company(
        id=uuid.uuid4(),
        name=f"Executor Corp {uuid.uuid4().hex[:6]}",
        slug=f"exec-corp-{uuid.uuid4().hex[:8]}",
        website_url="https://executor.example.com",
    )
    db.add(company)
    db.commit()

    sources = []
    for i in range(count):
        source = CareerSource(
            id=uuid.uuid4(),
            company_id=company.id,
            name=f"Source {i} - Greenhouse",
            source_type="greenhouse",
            base_url=f"https://boards.greenhouse.io/source{i}",
            is_active=is_active,
        )
        db.add(source)
        sources.append(source)
    db.commit()
    return sources


def test_concurrency_limit_enforced(db_session: Session):
    """Test that max_concurrency semaphore restricts simultaneous runs to the limit."""
    sources = create_multiple_sources(db_session, count=5)
    max_concurrency = 2
    settings = Settings(MONITORING_MAX_CONCURRENCY=max_concurrency)

    active_concurrent_count = 0
    max_observed_concurrent = 0

    async def mock_run_source(source_id, trigger_type=None):
        nonlocal active_concurrent_count, max_observed_concurrent
        active_concurrent_count += 1
        if active_concurrent_count > max_observed_concurrent:
            max_observed_concurrent = active_concurrent_count

        await asyncio.sleep(0.05)

        active_concurrent_count -= 1
        return MonitoringRun(
            id=uuid.uuid4(),
            career_source_id=source_id,
            status=MonitoringRunStatus.SUCCESS.value,
            trigger_type=MonitoringTriggerType.SCHEDULED.value,
        )

    service_mock = MagicMock(spec=MonitoringService)
    service_mock.run_source = AsyncMock(side_effect=mock_run_source)

    executor = MonitoringExecutor(service=service_mock, db=db_session, settings=settings)

    results = asyncio.run(executor.execute_all_active_sources())

    assert len(results) == 5
    assert max_observed_concurrent <= max_concurrency
    assert all(run is not None and run.status == MonitoringRunStatus.SUCCESS.value for _, run, _ in results)


def test_same_source_overlap_prevention(db_session: Session):
    """Test that triggering an already active source skips duplicate execution."""
    sources = create_multiple_sources(db_session, count=1)
    target_source = sources[0]

    service_mock = MagicMock(spec=MonitoringService)
    entered_event = asyncio.Event()
    release_event = asyncio.Event()

    async def slow_run_source(source_id, trigger_type=None):
        entered_event.set()
        await release_event.wait()
        return MonitoringRun(
            id=uuid.uuid4(),
            career_source_id=source_id,
            status=MonitoringRunStatus.SUCCESS.value,
        )

    service_mock.run_source = AsyncMock(side_effect=slow_run_source)
    executor = MonitoringExecutor(service=service_mock, db=db_session)

    async def scenario():
        # Start first run in background
        task1 = asyncio.create_task(executor.execute_source(target_source.id))
        await entered_event.wait()

        # Second trigger for the same source should be skipped
        run2, msg2 = await executor.execute_source(target_source.id)

        # Release first run
        release_event.set()
        run1, msg1 = await task1

        return (run1, msg1), (run2, msg2)

    (run1, msg1), (run2, msg2) = asyncio.run(scenario())

    assert run1 is not None
    assert run1.status == MonitoringRunStatus.SUCCESS.value
    assert run2 is None
    assert "already actively running" in msg2


def test_failure_isolation_across_sources(db_session: Session):
    """Test that an error in one source does not abort or impact remaining sources."""
    sources = create_multiple_sources(db_session, count=3)
    source_a, source_b, source_c = sources[0], sources[1], sources[2]

    service_mock = MagicMock(spec=MonitoringService)

    async def mock_run(source_id, trigger_type=None):
        if source_id == source_a.id:
            raise RuntimeError("Upstream connector crashed for source A")
        return MonitoringRun(
            id=uuid.uuid4(),
            career_source_id=source_id,
            status=MonitoringRunStatus.SUCCESS.value,
        )

    service_mock.run_source = AsyncMock(side_effect=mock_run)
    executor = MonitoringExecutor(service=service_mock, db=db_session)

    results = asyncio.run(executor.execute_all_active_sources())

    result_dict = {s_id: (run, msg) for s_id, run, msg in results}

    # Source A failed safely
    run_a, msg_a = result_dict[source_a.id]
    assert run_a is None
    assert "Upstream connector crashed" in msg_a

    # Sources B and C succeeded
    run_b, _ = result_dict[source_b.id]
    run_c, _ = result_dict[source_c.id]
    assert run_b is not None
    assert run_b.status == MonitoringRunStatus.SUCCESS.value
    assert run_c is not None
    assert run_c.status == MonitoringRunStatus.SUCCESS.value


def test_inactive_sources_skipped(db_session: Session):
    """Test that inactive sources return skipped without executing the service."""
    sources = create_multiple_sources(db_session, count=1, is_active=False)
    inactive_source = sources[0]

    service_mock = MagicMock(spec=MonitoringService)
    executor = MonitoringExecutor(service=service_mock, db=db_session)

    # In single source execution:
    run, msg = asyncio.run(executor.execute_source(inactive_source.id))
    assert run is None
    assert "inactive" in msg.lower()

    # In execute_all_active_sources, it shouldn't even be dispatched:
    results = asyncio.run(executor.execute_all_active_sources())
    assert len(results) == 0
