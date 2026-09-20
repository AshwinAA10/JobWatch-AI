"""Unit tests for MonitoringService orchestration, retry logic, and result recording."""

import asyncio
import uuid
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.orm import Session

from app.connectors.exceptions import ConnectorConfigurationError
from app.core.config import Settings
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.monitoring_run import MonitoringRunStatus, MonitoringTriggerType
from app.monitoring.exceptions import (
    SourceInactiveError,
    SourceNotFoundError,
)
from app.monitoring.service import MonitoringService
from app.services.ingestion import IngestionResult


def create_test_source(db: Session, is_active: bool = True) -> CareerSource:
    """Helper to create a company and career source."""
    company = Company(
        id=uuid.uuid4(),
        name="Service Test Corp",
        slug=f"svc-test-{uuid.uuid4().hex[:8]}",
        website_url="https://svctest.example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Service Test Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/svctest",
        is_active=is_active,
    )
    db.add(source)
    db.commit()
    return source


def test_monitoring_service_success(db_session: Session):
    """Test successful source monitoring execution."""
    source = create_test_source(db_session, is_active=True)
    service = MonitoringService(db=db_session)

    mock_result = IngestionResult(
        source_id=source.id,
        company_id=source.company_id,
        source_type="greenhouse",
        jobs_fetched=5,
        jobs_persisted=4,
        jobs_updated=1,
        jobs_skipped=0,
        errors=[],
        duration_seconds=0.15,
    )

    with patch(
        "app.services.ingestion.JobIngestionService.ingest_source",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        run = asyncio.run(
            service.run_source(source.id, trigger_type=MonitoringTriggerType.SCHEDULED.value)
        )

    assert run.status == MonitoringRunStatus.SUCCESS.value
    assert run.career_source_id == source.id
    assert run.trigger_type == MonitoringTriggerType.SCHEDULED.value
    assert run.jobs_fetched == 5
    assert run.jobs_created == 4
    assert run.jobs_updated == 1
    assert run.jobs_skipped == 0
    assert run.error_count == 0
    assert run.started_at is not None
    assert run.completed_at is not None
    assert run.attempt == 1


def test_monitoring_service_partial_success(db_session: Session):
    """Test monitoring execution with skipped jobs maps to PARTIAL_SUCCESS."""
    source = create_test_source(db_session, is_active=True)
    service = MonitoringService(db=db_session)

    mock_result = IngestionResult(
        source_id=source.id,
        company_id=source.company_id,
        source_type="greenhouse",
        jobs_fetched=10,
        jobs_persisted=7,
        jobs_updated=0,
        jobs_skipped=3,
        errors=["Missing required field in job 123"],
        duration_seconds=0.25,
    )

    with patch(
        "app.services.ingestion.JobIngestionService.ingest_source",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        run = asyncio.run(
            service.run_source(source.id, trigger_type=MonitoringTriggerType.MANUAL.value)
        )

    assert run.status == MonitoringRunStatus.PARTIAL_SUCCESS.value
    assert run.trigger_type == MonitoringTriggerType.MANUAL.value
    assert run.jobs_fetched == 10
    assert run.jobs_created == 7
    assert run.jobs_skipped == 3
    assert run.error_count == 1
    assert "Missing required field" in (run.error_message or "")


def test_monitoring_service_transient_retry_and_recovery(db_session: Session):
    """Verify that transient failures are retried and can recover successfully."""
    source = create_test_source(db_session, is_active=True)

    fast_retry_settings = Settings(
        MONITORING_MAX_RETRIES=2,
        MONITORING_RETRY_BACKOFF_SECONDS=0.01,
        MONITORING_SOURCE_TIMEOUT_SECONDS=5,
    )
    service = MonitoringService(db=db_session, settings=fast_retry_settings)

    mock_success = IngestionResult(
        source_id=source.id,
        jobs_fetched=2,
        jobs_persisted=2,
        jobs_updated=0,
        jobs_skipped=0,
        errors=[],
    )

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionResetError("Connection dropped by remote server")
        return mock_success

    with patch(
        "app.services.ingestion.JobIngestionService.ingest_source",
        new_callable=AsyncMock,
        side_effect=side_effect,
    ):
        run = asyncio.run(service.run_source(source.id))

    assert call_count == 2
    assert run.status == MonitoringRunStatus.SUCCESS.value
    assert run.attempt == 2
    assert run.jobs_created == 2


def test_monitoring_service_permanent_error_no_retry(db_session: Session):
    """Configuration/unsupported connector errors must fail immediately without retrying."""
    source = create_test_source(db_session, is_active=True)

    fast_retry_settings = Settings(
        MONITORING_MAX_RETRIES=3,
        MONITORING_RETRY_BACKOFF_SECONDS=0.01,
        MONITORING_SOURCE_TIMEOUT_SECONDS=5,
    )
    service = MonitoringService(db=db_session, settings=fast_retry_settings)

    with patch(
        "app.services.ingestion.JobIngestionService.ingest_source",
        new_callable=AsyncMock,
        side_effect=ConnectorConfigurationError("Invalid API token credentials"),
    ) as mock_ingest:
        run = asyncio.run(service.run_source(source.id))

    # Should only execute once
    assert mock_ingest.call_count == 1
    assert run.status == MonitoringRunStatus.FAILED.value
    assert run.attempt == 1
    assert "Invalid API token credentials" in (run.error_message or "")


def test_monitoring_service_all_retries_exhausted(db_session: Session):
    """When all transient retries fail, run status transitions to FAILED."""
    source = create_test_source(db_session, is_active=True)

    fast_retry_settings = Settings(
        MONITORING_MAX_RETRIES=2,
        MONITORING_RETRY_BACKOFF_SECONDS=0.01,
        MONITORING_SOURCE_TIMEOUT_SECONDS=5,
    )
    service = MonitoringService(db=db_session, settings=fast_retry_settings)

    with patch(
        "app.services.ingestion.JobIngestionService.ingest_source",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Persistent upstream outage"),
    ) as mock_ingest:
        run = asyncio.run(service.run_source(source.id))

    assert mock_ingest.call_count == 3  # Initial attempt + 2 retries
    assert run.status == MonitoringRunStatus.FAILED.value
    assert run.attempt == 3
    assert "Persistent upstream outage" in (run.error_message or "")


def test_monitoring_service_inactive_source_rejected(db_session: Session):
    """Attempting to run an inactive source must raise SourceInactiveError."""
    source = create_test_source(db_session, is_active=False)
    service = MonitoringService(db=db_session)

    with pytest.raises(SourceInactiveError):
        asyncio.run(service.run_source(source.id))


def test_monitoring_service_missing_source_rejected(db_session: Session):
    """Attempting to run a non-existent source must raise SourceNotFoundError."""
    service = MonitoringService(db=db_session)
    non_existent_id = uuid.uuid4()

    with pytest.raises(SourceNotFoundError):
        asyncio.run(service.run_source(non_existent_id))
