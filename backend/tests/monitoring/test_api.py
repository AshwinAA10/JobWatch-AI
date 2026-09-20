"""Integration and API tests for monitoring endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.monitoring_run import MonitoringRun, MonitoringRunStatus, MonitoringTriggerType
from app.monitoring.scheduler import MonitoringScheduler, get_scheduler
from app.repositories.monitoring_run import MonitoringRunRepository


def create_test_company_and_source(db: Session, is_active: bool = True) -> CareerSource:
    """Helper to create a company and career source."""
    company = Company(
        id=uuid.uuid4(),
        name=f"API Test Corp {uuid.uuid4().hex[:6]}",
        slug=f"api-corp-{uuid.uuid4().hex[:8]}",
        website_url="https://apicorp.example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="API Test Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/apicorp",
        is_active=is_active,
    )
    db.add(source)
    db.commit()
    return source


def test_get_monitoring_status(client: TestClient):
    """Test GET /api/v1/monitoring/status returns expected health and config state."""
    response = client.get("/api/v1/monitoring/status")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "enabled" in data
    assert "running" in data
    assert "interval_seconds" in data
    assert "max_concurrency" in data
    assert "active_sources_count" in data


def test_trigger_source_run_success(client: TestClient, db_session: Session):
    """Test POST /api/v1/monitoring/run/{source_id} triggers execution for active source."""
    source = create_test_company_and_source(db_session, is_active=True)

    fake_run = MonitoringRun(
        id=uuid.uuid4(),
        career_source_id=source.id,
        status=MonitoringRunStatus.SUCCESS.value,
        trigger_type=MonitoringTriggerType.MANUAL.value,
    )

    mock_scheduler = MagicMock(spec=MonitoringScheduler)
    mock_scheduler.executor = MagicMock()
    mock_scheduler.executor.execute_source = AsyncMock(
        return_value=(fake_run, "Execution completed with status SUCCESS")
    )

    app.dependency_overrides[get_scheduler] = lambda: mock_scheduler
    try:
        response = client.post(f"/api/v1/monitoring/run/{source.id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["source_id"] == str(source.id)
        assert data["run_id"] == str(fake_run.id)
        assert data["status"] == MonitoringRunStatus.SUCCESS.value
    finally:
        app.dependency_overrides.pop(get_scheduler, None)


def test_trigger_source_run_inactive(client: TestClient, db_session: Session):
    """Test POST /api/v1/monitoring/run/{source_id} rejects inactive sources with 400."""
    source = create_test_company_and_source(db_session, is_active=False)

    response = client.post(f"/api/v1/monitoring/run/{source.id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "inactive" in response.json()["detail"].lower()


def test_trigger_source_run_not_found(client: TestClient):
    """Test POST /api/v1/monitoring/run/{source_id} returns 404 for missing source."""
    random_id = uuid.uuid4()
    response = client.post(f"/api/v1/monitoring/run/{random_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_trigger_all_sources_run(client: TestClient):
    """Test POST /api/v1/monitoring/run-all triggers all active sources."""
    source_id1 = uuid.uuid4()
    source_id2 = uuid.uuid4()

    fake_run = MonitoringRun(
        id=uuid.uuid4(),
        career_source_id=source_id1,
        status=MonitoringRunStatus.SUCCESS.value,
    )

    mock_results = [
        (source_id1, fake_run, "Success"),
        (source_id2, None, "Already running"),
    ]

    mock_scheduler = MagicMock(spec=MonitoringScheduler)
    mock_scheduler.trigger_cycle = AsyncMock(return_value=mock_results)

    app.dependency_overrides[get_scheduler] = lambda: mock_scheduler
    try:
        response = client.post("/api/v1/monitoring/run-all")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["triggered_count"] == 1
        assert data["skipped_count"] == 1
        assert str(source_id1) in data["sources_triggered"]
        assert str(source_id2) in data["sources_skipped"]
    finally:
        app.dependency_overrides.pop(get_scheduler, None)


def test_list_monitoring_runs(client: TestClient, db_session: Session):
    """Test GET /api/v1/monitoring/runs with filters and pagination."""
    source = create_test_company_and_source(db_session)
    run_repo = MonitoringRunRepository(db_session)

    run1 = run_repo.create(
        career_source_id=source.id,
        status=MonitoringRunStatus.SUCCESS.value,
        trigger_type=MonitoringTriggerType.SCHEDULED.value,
    )
    run2 = run_repo.create(
        career_source_id=source.id,
        status=MonitoringRunStatus.FAILED.value,
        trigger_type=MonitoringTriggerType.MANUAL.value,
    )

    # 1. Fetch all
    response = client.get("/api/v1/monitoring/runs")
    assert response.status_code == status.HTTP_200_OK
    runs = response.json()
    assert len(runs) >= 2

    # 2. Filter by status
    response = client.get("/api/v1/monitoring/runs?status=SUCCESS")
    assert response.status_code == status.HTTP_200_OK
    runs = response.json()
    assert all(r["status"] == "SUCCESS" for r in runs)

    # 3. Filter by career_source_id
    response = client.get(f"/api/v1/monitoring/runs?career_source_id={source.id}")
    assert response.status_code == status.HTTP_200_OK
    runs = response.json()
    assert len(runs) == 2

    # 4. Pagination
    response = client.get(f"/api/v1/monitoring/runs?career_source_id={source.id}&limit=1")
    assert response.status_code == status.HTTP_200_OK
    runs = response.json()
    assert len(runs) == 1
