"""End-to-end integration test connecting MonitoringService -> JobIngestionService -> Database."""

import asyncio
from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.monitoring_run import MonitoringRunStatus, MonitoringTriggerType
from app.monitoring.service import MonitoringService
from app.repositories.job import JobRepository
from app.repositories.monitoring_run import MonitoringRunRepository
from app.connectors.models import NormalizedJob


def test_monitoring_ingestion_end_to_end(db_session: Session):
    """Verify full workflow: CareerSource -> MonitoringService -> Mock Connector -> Ingestion -> DB -> MonitoringRun."""
    # 1. Seed Company and CareerSource
    company = Company(
        id=uuid.uuid4(),
        name="Integration Tech",
        slug=f"integ-tech-{uuid.uuid4().hex[:8]}",
        website_url="https://integration.example.com",
    )
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Integration Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/integrationtech",
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()

    # 2. Mock external connector to return NormalizedJobs
    fake_jobs = [
        NormalizedJob(
            external_id="gh-101",
            title="Senior Backend Engineer",
            url="https://boards.greenhouse.io/integrationtech/jobs/101",
            location="Remote",
            description="Build scalable distributed services in Python.",
            department="Engineering",
            posted_at=datetime.now(timezone.utc),
            metadata={"board": "integrationtech"},
        ),
        NormalizedJob(
            external_id="gh-102",
            title="Lead DevOps Architect",
            url="https://boards.greenhouse.io/integrationtech/jobs/102",
            location="New York, NY",
            description="Manage cloud infrastructure and CI/CD.",
            department="Operations",
            posted_at=datetime.now(timezone.utc),
            metadata={"board": "integrationtech"},
        ),
    ]

    service = MonitoringService(db=db_session)

    # Patch the connector fetch method
    with patch(
        "app.connectors.greenhouse.GreenhouseConnector.fetch_jobs",
        new_callable=AsyncMock,
        return_value=fake_jobs,
    ):
        run = asyncio.run(
            service.run_source(
                source_id=source.id,
                trigger_type=MonitoringTriggerType.SCHEDULED.value,
            )
        )

    # 3. Verify MonitoringRun state and metrics
    assert run.status == MonitoringRunStatus.SUCCESS.value
    assert run.career_source_id == source.id
    assert run.trigger_type == MonitoringTriggerType.SCHEDULED.value
    assert run.jobs_fetched == 2
    assert run.jobs_created == 2
    assert run.jobs_updated == 0
    assert run.jobs_skipped == 0
    assert run.error_count == 0
    assert run.started_at is not None
    assert run.completed_at is not None

    # 4. Verify persisted jobs in Database via JobRepository
    job_repo = JobRepository(db_session)
    persisted_job_1 = job_repo.get_by_external_id(source.id, "gh-101")
    persisted_job_2 = job_repo.get_by_external_id(source.id, "gh-102")

    assert persisted_job_1 is not None
    assert persisted_job_1.title == "Senior Backend Engineer"
    assert persisted_job_1.company_id == company.id

    assert persisted_job_2 is not None
    assert persisted_job_2.title == "Lead DevOps Architect"
    assert persisted_job_2.company_id == company.id

    # 5. Verify MonitoringRun can be retrieved from repository
    run_repo = MonitoringRunRepository(db_session)
    fetched_run = run_repo.get_by_id(run.id)
    assert fetched_run is not None
    assert fetched_run.status == MonitoringRunStatus.SUCCESS.value
