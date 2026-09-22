"""Tests for candidate blocking and O(N^2) global scan prevention."""

from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.deduplication.service import DeduplicationService
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job


def seed_company_and_source(db: Session, name_prefix: str) -> tuple:
    """Create test company and career source."""
    company = Company(
        id=uuid.uuid4(),
        name=f"{name_prefix} Corp",
        slug=f"{name_prefix.lower()}-{uuid.uuid4().hex[:8]}",
        website_url="https://example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name=f"{name_prefix} Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/test",
        is_active=True,
    )
    db.add(source)
    db.commit()
    return company, source


def test_candidate_blocking_isolates_by_company(db_session: Session):
    """Verify candidate search only queries jobs belonging to the same company."""
    company_a, source_a = seed_company_and_source(db_session, "CompanyA")
    company_b, source_b = seed_company_and_source(db_session, "CompanyB")

    # Seed 10 jobs for Company B
    for i in range(10):
        db_session.add(
            Job(
                company_id=company_b.id,
                career_source_id=source_b.id,
                external_id=f"comp-b-{i}",
                title=f"Engineer {i}",
                first_seen_at=datetime.now(timezone.utc),
            )
        )

    # Seed target job and 2 candidates for Company A
    job_target = Job(
        company_id=company_a.id,
        career_source_id=source_a.id,
        external_id="comp-a-target",
        title="Target Engineer",
        first_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(job_target)

    for i in range(2):
        db_session.add(
            Job(
                company_id=company_a.id,
                career_source_id=source_a.id,
                external_id=f"comp-a-cand-{i}",
                title=f"Candidate Engineer {i}",
                first_seen_at=datetime.now(timezone.utc),
            )
        )
    db_session.commit()

    service = DeduplicationService(db_session)
    candidates = service.get_candidates(job_target)

    # Must only retrieve the 2 candidates from Company A, completely ignoring Company B
    assert len(candidates) == 2
    assert all(c.company_id == company_a.id for c in candidates)
    assert all(c.id != job_target.id for c in candidates)


def test_candidate_blocking_respects_limits(db_session: Session):
    """Verify candidate retrieval enforces DEDUP_MAX_CANDIDATES limit."""
    company, source = seed_company_and_source(db_session, "LimitTest")

    target = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="target",
        title="Target Job",
        first_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(target)

    for i in range(15):
        db_session.add(
            Job(
                company_id=company.id,
                career_source_id=source.id,
                external_id=f"cand-{i}",
                title=f"Job {i}",
                first_seen_at=datetime.now(timezone.utc),
            )
        )
    db_session.commit()

    settings = Settings(DEDUP_MAX_CANDIDATES=5)
    service = DeduplicationService(db_session, settings=settings)

    candidates = service.get_candidates(target)
    assert len(candidates) == 5


def test_candidate_blocking_respects_lookback_window(db_session: Session):
    """Jobs older than lookback days are excluded from candidate retrieval."""
    company, source = seed_company_and_source(db_session, "LookbackTest")

    now = datetime.now(timezone.utc)
    target = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="target",
        title="Target Job",
        first_seen_at=now,
    )
    db_session.add(target)

    # 1 recent candidate (5 days old)
    recent = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="recent",
        title="Recent Candidate",
        first_seen_at=now - timedelta(days=5),
    )
    db_session.add(recent)

    # 1 ancient candidate (120 days old)
    ancient = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id="ancient",
        title="Ancient Candidate",
        first_seen_at=now - timedelta(days=120),
    )
    db_session.add(ancient)
    db_session.commit()

    settings = Settings(DEDUP_LOOKBACK_DAYS=30)
    service = DeduplicationService(db_session, settings=settings)

    candidates = service.get_candidates(target)
    assert len(candidates) == 1
    assert candidates[0].external_id == "recent"
