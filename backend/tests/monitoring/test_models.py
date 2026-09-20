"""Unit tests for MonitoringRun model and database relationships."""

import uuid
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.career_source import CareerSource
from app.models.monitoring_run import (
    MonitoringRun,
    MonitoringRunStatus,
    MonitoringTriggerType,
)


def create_test_company_and_source(db: Session) -> CareerSource:
    """Helper to create a parent company and career source."""
    company = Company(
        id=uuid.uuid4(),
        name="Model Test Corp",
        slug=f"model-test-{uuid.uuid4().hex[:8]}",
        website_url="https://modeltest.example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Model Test Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/modeltest",
        is_active=True,
    )
    db.add(source)
    db.commit()
    return source


def test_monitoring_run_creation(db_session: Session):
    """Verify MonitoringRun is created with valid defaults and timestamps."""
    source = create_test_company_and_source(db_session)

    run = MonitoringRun(
        career_source_id=source.id,
        status=MonitoringRunStatus.PENDING.value,
        trigger_type=MonitoringTriggerType.SCHEDULED.value,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    assert run.id is not None
    assert run.career_source_id == source.id
    assert run.status == "PENDING"
    assert run.trigger_type == "SCHEDULED"
    assert run.jobs_fetched == 0
    assert run.jobs_created == 0
    assert run.jobs_updated == 0
    assert run.jobs_skipped == 0
    assert run.error_count == 0
    assert run.attempt == 1
    assert run.created_at is not None
    assert run.updated_at is not None
    assert run.started_at is None
    assert run.completed_at is None


def test_monitoring_run_relationships(db_session: Session):
    """Verify bidirectional relationship between CareerSource and MonitoringRun."""
    source = create_test_company_and_source(db_session)

    run = MonitoringRun(
        career_source_id=source.id,
        status=MonitoringRunStatus.RUNNING.value,
        trigger_type=MonitoringTriggerType.MANUAL.value,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(source)
    db_session.refresh(run)

    assert run.career_source.id == source.id
    assert len(source.monitoring_runs) == 1
    assert source.monitoring_runs[0].id == run.id


def test_cascade_delete_source_removes_monitoring_runs(db_session: Session):
    """Verify deleting a CareerSource cascades and removes its monitoring runs."""
    source = create_test_company_and_source(db_session)
    source_id = source.id

    run = MonitoringRun(
        career_source_id=source.id,
        status=MonitoringRunStatus.SUCCESS.value,
    )
    db_session.add(run)
    db_session.commit()
    run_id = run.id

    # Delete the parent source
    db_session.delete(source)
    db_session.commit()

    # The run must no longer exist
    assert db_session.get(MonitoringRun, run_id) is None
