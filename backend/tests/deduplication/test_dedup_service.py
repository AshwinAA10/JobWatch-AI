"""Unit tests for DeduplicationService canonical resolution, linking, and cycle prevention."""

from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.deduplication.exceptions import JobNotFoundError
from app.deduplication.service import DeduplicationService
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_duplicate import MatchType


def seed_company_and_two_sources(db: Session):
    """Seed test company and two distinct career sources (e.g. Greenhouse and Lever)."""
    company = Company(
        id=uuid.uuid4(),
        name="TechCorp",
        slug=f"techcorp-{uuid.uuid4().hex[:8]}",
        website_url="https://techcorp.example.com",
    )
    db.add(company)
    db.commit()

    source_gh = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="TechCorp Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/techcorp",
        is_active=True,
    )
    source_lever = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="TechCorp Lever",
        source_type="lever",
        base_url="https://jobs.lever.co/techcorp",
        is_active=True,
    )
    db.add(source_gh)
    db.add(source_lever)
    db.commit()
    return company, source_gh, source_lever


def test_deduplicate_job_creates_relationship_and_preserves_both(db_session: Session):
    """Verify that duplicate is linked to canonical without deleting either job."""
    company, source_gh, source_lever = seed_company_and_two_sources(db_session)

    now = datetime.now(timezone.utc)
    # Job A discovered on Greenhouse 5 days ago (Canonical candidate)
    job_a = Job(
        company_id=company.id,
        career_source_id=source_gh.id,
        external_id="gh-500",
        title="Senior Python Architect",
        location="Bengaluru, India",
        workplace_type="remote",
        employment_type="full-time",
        application_url="https://boards.greenhouse.io/techcorp/jobs/500",
        source_url="https://boards.greenhouse.io/techcorp/jobs/500",
        description="Lead backend architecture with Python and distributed systems.",
        first_seen_at=now - timedelta(days=5),
    )
    # Job B discovered on Lever today (Duplicate candidate)
    job_b = Job(
        company_id=company.id,
        career_source_id=source_lever.id,
        external_id="lever-900",
        title="Senior Python Architect",
        location="Bangalore",
        workplace_type="remote",
        employment_type="full-time",
        application_url="https://jobs.lever.co/techcorp/900",
        source_url="https://jobs.lever.co/techcorp/900",
        description="Lead backend architecture with Python and distributed microservices.",
        first_seen_at=now,
    )
    db_session.add(job_a)
    db_session.add(job_b)
    db_session.commit()

    service = DeduplicationService(db_session)
    dup_record = service.deduplicate_job(job_b.id)

    assert dup_record is not None
    assert dup_record.canonical_job_id == job_a.id
    assert dup_record.duplicate_job_id == job_b.id
    assert dup_record.confidence_score >= 0.90

    # Refresh jobs from DB
    db_session.refresh(job_a)
    db_session.refresh(job_b)

    # Both job rows MUST be preserved
    assert job_a is not None
    assert job_b is not None
    assert job_a.canonical_job_id is None  # Canonical root
    assert job_b.canonical_job_id == job_a.id  # Linked duplicate
    assert job_b.career_source_id == source_lever.id  # Source provenance intact


def test_canonical_root_resolution_prevents_chaining(db_session: Session):
    """When a new duplicate matches an existing duplicate, it must link to root canonical."""
    company, source_gh, source_lever = seed_company_and_two_sources(db_session)

    now = datetime.now(timezone.utc)
    job_root = Job(
        company_id=company.id,
        career_source_id=source_gh.id,
        external_id="root-1",
        title="Principal DevOps Engineer",
        first_seen_at=now - timedelta(days=10),
    )
    job_dup1 = Job(
        company_id=company.id,
        career_source_id=source_lever.id,
        external_id="dup-1",
        title="Principal DevOps Engineer",
        canonical_job_id=None,  # Will be set to job_root
        first_seen_at=now - timedelta(days=5),
    )
    db_session.add(job_root)
    db_session.add(job_dup1)
    db_session.commit()

    # Link dup1 to root
    job_dup1.canonical_job_id = job_root.id
    db_session.commit()

    service = DeduplicationService(db_session)
    resolved_root = service.resolve_canonical_root(job_dup1)
    assert resolved_root.id == job_root.id


def test_disabled_dedup_flag(db_session: Session):
    """When DEDUP_ENABLED is False, no deduplication analysis is executed."""
    company, source_gh, _ = seed_company_and_two_sources(db_session)
    job = Job(
        company_id=company.id,
        career_source_id=source_gh.id,
        external_id="disabled-job",
        title="Frontend Engineer",
    )
    db_session.add(job)
    db_session.commit()

    settings = Settings(DEDUP_ENABLED=False)
    service = DeduplicationService(db_session, settings=settings)
    result = service.deduplicate_job(job.id)
    assert result is None


def test_deduplicate_missing_job_raises(db_session: Session):
    """Deduplicating non-existent job ID raises JobNotFoundError."""
    service = DeduplicationService(db_session)
    import pytest
    with pytest.raises(JobNotFoundError):
        service.deduplicate_job(uuid.uuid4())


def test_medium_confidence_not_auto_merged(db_session: Session):
    """Verify that jobs with subtle specialization differences (medium confidence) are not auto-merged."""
    company, source_gh, source_lever = seed_company_and_two_sources(db_session)

    now = datetime.now(timezone.utc)
    job_backend = Job(
        company_id=company.id,
        career_source_id=source_gh.id,
        external_id="gh-back",
        title="Software Engineer - Backend",
        location="Bengaluru",
        first_seen_at=now - timedelta(days=2),
    )
    job_infra = Job(
        company_id=company.id,
        career_source_id=source_lever.id,
        external_id="lever-infra",
        title="Software Engineer - Infrastructure",
        location="Bengaluru",
        first_seen_at=now,
    )
    db_session.add(job_backend)
    db_session.add(job_infra)
    db_session.commit()

    service = DeduplicationService(db_session)
    result = service.deduplicate_job(job_infra.id)

    # Must NOT auto-merge since title difference brings it below 0.90
    assert result is None
    db_session.refresh(job_infra)
    assert job_infra.canonical_job_id is None

