"""End-to-end integration test: Multi-Source Ingestion -> Batch Deduplication -> Canonical Linking."""

import asyncio
from datetime import datetime, timezone
import uuid
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.connectors.models import NormalizedJob
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_duplicate import JobDuplicate
from app.services.ingestion import JobIngestionService


def test_cross_source_ingestion_and_deduplication_e2e(db_session: Session):
    """Verify that multi-source ingestion automatically detects cross-source duplicates and establishes canonical links."""
    # 1. Create Company and 2 distinct career sources (Greenhouse + Lever)
    company = Company(
        id=uuid.uuid4(),
        name="Integration Enterprise",
        slug=f"integ-ent-{uuid.uuid4().hex[:8]}",
        website_url="https://integration.enterprise.com",
    )
    db_session.add(company)
    db_session.commit()

    source_gh = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Enterprise Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/enterprise",
        is_active=True,
    )
    source_lever = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Enterprise Lever",
        source_type="lever",
        base_url="https://jobs.lever.co/enterprise",
        is_active=True,
    )
    db_session.add(source_gh)
    db_session.add(source_lever)
    db_session.commit()

    # 2. Ingest Greenhouse source with initial jobs
    gh_jobs = [
        NormalizedJob(
            external_id="gh-role-1",
            title="Senior Distributed Systems Engineer",
            application_url="https://boards.greenhouse.io/enterprise/jobs/role-1",
            location="Bengaluru, India",
            workplace_type="remote",
            employment_type="full-time",
            description="Architect robust distributed services in Python and Go.",
            posted_at=datetime.now(timezone.utc),
        ),
    ]

    ingestion_service = JobIngestionService(db_session)

    with patch(
        "app.connectors.greenhouse.GreenhouseConnector.fetch_jobs",
        new_callable=AsyncMock,
        return_value=gh_jobs,
    ):
        result_gh = asyncio.run(ingestion_service.ingest_source(source_gh.id))

    assert result_gh.jobs_persisted == 1

    # Fetch canonical Greenhouse job
    canonical_job = (
        db_session.query(Job)
        .filter(Job.career_source_id == source_gh.id)
        .first()
    )
    assert canonical_job is not None
    assert canonical_job.canonical_job_id is None

    # 3. Ingest Lever source with the same real-world job posting (identical normalized title & location)
    lever_jobs = [
        NormalizedJob(
            external_id="lever-role-101",
            title="Senior Distributed Systems Engineer",
            application_url="https://jobs.lever.co/enterprise/role-101",
            location="Bangalore",
            workplace_type="remote",
            employment_type="full-time",
            description="Architect robust distributed services in Python and Go.",
            posted_at=datetime.now(timezone.utc),
        ),
    ]

    with patch(
        "app.connectors.lever.LeverConnector.fetch_jobs",
        new_callable=AsyncMock,
        return_value=lever_jobs,
    ):
        result_lever = asyncio.run(ingestion_service.ingest_source(source_lever.id))

    assert result_lever.jobs_persisted == 1

    # Fetch Lever job
    duplicate_job = (
        db_session.query(Job)
        .filter(Job.career_source_id == source_lever.id)
        .first()
    )
    assert duplicate_job is not None

    # 4. Verify Canonical Linking & Data Preservation
    db_session.refresh(canonical_job)
    db_session.refresh(duplicate_job)

    # Both jobs MUST exist in database
    assert canonical_job.id != duplicate_job.id
    assert canonical_job.career_source_id == source_gh.id
    assert duplicate_job.career_source_id == source_lever.id

    # Canonical link
    assert canonical_job.canonical_job_id is None
    assert duplicate_job.canonical_job_id == canonical_job.id

    # JobDuplicate record check
    dup_record = (
        db_session.query(JobDuplicate)
        .filter(JobDuplicate.duplicate_job_id == duplicate_job.id)
        .first()
    )
    assert dup_record is not None
    assert dup_record.canonical_job_id == canonical_job.id
    assert dup_record.confidence_score >= 0.90
