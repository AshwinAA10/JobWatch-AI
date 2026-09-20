"""Unit tests for MonitoringRunRepository operations."""

from datetime import datetime, timezone, timedelta
import uuid
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.monitoring_run import MonitoringRunStatus, MonitoringTriggerType
from app.repositories.monitoring_run import MonitoringRunRepository


def create_test_company_and_source(db: Session) -> CareerSource:
    """Helper to create a parent company and career source."""
    company = Company(
        id=uuid.uuid4(),
        name="Repo Test Corp",
        slug=f"repo-test-{uuid.uuid4().hex[:8]}",
        website_url="https://repotest.example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Repo Test Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/repotest",
        is_active=True,
    )
    db.add(source)
    db.commit()
    return source


def test_create_and_get_by_id(db_session: Session):
    """Verify create and get_by_id on MonitoringRunRepository."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    run = repo.create(
        career_source_id=source.id,
        trigger_type=MonitoringTriggerType.MANUAL.value,
        status=MonitoringRunStatus.PENDING.value,
    )
    assert run.id is not None
    assert run.status == "PENDING"
    assert run.trigger_type == "MANUAL"

    fetched = repo.get_by_id(run.id)
    assert fetched is not None
    assert fetched.id == run.id


def test_mark_running(db_session: Session):
    """Verify transitioning run to RUNNING sets started_at."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    run = repo.create(career_source_id=source.id)
    assert run.status == "PENDING"
    assert run.started_at is None

    updated = repo.mark_running(run)
    assert updated.status == "RUNNING"
    assert updated.started_at is not None


def test_complete_run(db_session: Session):
    """Verify complete_run sets status, metrics, and completed_at."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    run = repo.create(career_source_id=source.id)
    repo.mark_running(run)

    completed = repo.complete_run(
        run=run,
        status=MonitoringRunStatus.SUCCESS.value,
        jobs_fetched=25,
        jobs_created=20,
        jobs_updated=5,
        jobs_skipped=0,
        error_count=0,
    )

    assert completed.status == "SUCCESS"
    assert completed.jobs_fetched == 25
    assert completed.jobs_created == 20
    assert completed.jobs_updated == 5
    assert completed.jobs_skipped == 0
    assert completed.completed_at is not None


def test_mark_failed(db_session: Session):
    """Verify mark_failed transitions to FAILED and records error message."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    run = repo.create(career_source_id=source.id)
    repo.mark_running(run)

    failed = repo.mark_failed(
        run=run,
        error_message="HTTP 502 Bad Gateway from career portal",
        error_count=2,
    )

    assert failed.status == "FAILED"
    assert failed.error_message == "HTTP 502 Bad Gateway from career portal"
    assert failed.error_count == 2
    assert failed.completed_at is not None


def test_get_active_run_for_source(db_session: Session):
    """Verify active run detection returns PENDING/RUNNING runs and ignores completed runs."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    # No run initially
    assert repo.get_active_run_for_source(source.id) is None

    # Create active run
    run = repo.create(career_source_id=source.id)
    active = repo.get_active_run_for_source(source.id)
    assert active is not None
    assert active.id == run.id

    # Once completed, it is no longer active
    repo.complete_run(run, status=MonitoringRunStatus.SUCCESS.value)
    assert repo.get_active_run_for_source(source.id) is None


def test_list_runs_filtering_and_pagination(db_session: Session):
    """Verify filtering and pagination in list_runs."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    # Create 3 runs: 2 SUCCESS, 1 FAILED
    r1 = repo.create(career_source_id=source.id)
    repo.complete_run(r1, status=MonitoringRunStatus.SUCCESS.value)

    r2 = repo.create(career_source_id=source.id)
    repo.mark_failed(r2, error_message="Error")

    r3 = repo.create(career_source_id=source.id)
    repo.complete_run(r3, status=MonitoringRunStatus.SUCCESS.value)

    # List all for source
    all_runs = repo.list_runs(career_source_id=source.id)
    assert len(all_runs) == 3

    # Filter by status
    success_runs = repo.list_runs(career_source_id=source.id, status=MonitoringRunStatus.SUCCESS.value)
    assert len(success_runs) == 2

    # Pagination: limit=1
    paginated = repo.list_runs(career_source_id=source.id, limit=1)
    assert len(paginated) == 1


def test_list_stale_runs(db_session: Session):
    """Verify detection of runs running past a duration threshold."""
    source = create_test_company_and_source(db_session)
    repo = MonitoringRunRepository(db_session)

    run = repo.create(career_source_id=source.id)
    repo.mark_running(run)

    # Manually backdate started_at to 2 hours ago
    run.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.commit()

    stale_runs = repo.list_stale_runs(threshold_seconds=3600)  # > 1 hour
    assert len(stale_runs) == 1
    assert stale_runs[0].id == run.id
