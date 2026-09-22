"""API integration tests for Deduplication endpoints."""

from datetime import datetime, timezone
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_duplicate import MatchType
from app.repositories.job_duplicate import JobDuplicateRepository


def create_test_jobs_and_sources(db: Session):
    """Seed test company, sources, and jobs."""
    company = Company(
        id=uuid.uuid4(),
        name=f"API Dedup Corp {uuid.uuid4().hex[:6]}",
        slug=f"api-dedup-{uuid.uuid4().hex[:8]}",
        website_url="https://apidedup.example.com",
    )
    db.add(company)
    db.commit()

    source1 = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Source 1",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/corp",
        is_active=True,
    )
    source2 = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Source 2",
        source_type="lever",
        base_url="https://jobs.lever.co/corp",
        is_active=True,
    )
    db.add(source1)
    db.add(source2)
    db.commit()

    job1 = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source1.id,
        external_id="gh-1",
        title="Senior Cloud Architect",
        location="Bengaluru",
        first_seen_at=datetime.now(timezone.utc),
    )
    job2 = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source2.id,
        external_id="lever-1",
        title="Senior Cloud Architect",
        location="Bengaluru",
        first_seen_at=datetime.now(timezone.utc),
    )
    db.add(job1)
    db.add(job2)
    db.commit()

    return company, job1, job2


def test_get_dedup_status(client: TestClient):
    """Verify GET /api/v1/dedup/status returns configuration."""
    response = client.get("/api/v1/dedup/status")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "enabled" in data
    assert "high_threshold" in data
    assert "medium_threshold" in data
    assert "max_candidates" in data
    assert "lookback_days" in data


def test_list_duplicates_and_filter(client: TestClient, db_session: Session):
    """Verify GET /api/v1/dedup/duplicates returns duplicate list with pagination and filtering."""
    _, job1, job2 = create_test_jobs_and_sources(db_session)
    repo = JobDuplicateRepository(db_session)

    record = repo.create(
        canonical_job_id=job1.id,
        duplicate_job_id=job2.id,
        match_type=MatchType.HIGH_CONFIDENCE.value,
        confidence_score=0.95,
        reason="High similarity",
    )

    # List all
    response = client.get("/api/v1/dedup/duplicates")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1

    # Filter by canonical_id
    response = client.get(f"/api/v1/dedup/duplicates?canonical_id={job1.id}")
    assert response.status_code == status.HTTP_200_OK
    filtered = response.json()
    assert len(filtered) == 1
    assert filtered[0]["id"] == str(record.id)


def test_run_job_deduplication_success(client: TestClient, db_session: Session):
    """Verify POST /api/v1/dedup/run/{job_id} detects duplicate against existing job."""
    _, job1, job2 = create_test_jobs_and_sources(db_session)

    response = client.post(f"/api/v1/dedup/run/{job2.id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["job_id"] == str(job2.id)
    assert data["is_duplicate"] is True
    assert data["canonical_job_id"] == str(job1.id)
    assert data["confidence_score"] >= 0.90


def test_run_job_deduplication_not_found(client: TestClient):
    """Verify POST /api/v1/dedup/run/{job_id} returns 404 for non-existent job."""
    missing_id = uuid.uuid4()
    response = client.post(f"/api/v1/dedup/run/{missing_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
