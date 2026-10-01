"""API tests for job discovery, search, filtering, detail, and bookmarks."""

import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_match import JobMatch
from app.models.user import User


def _get_auth_header(client: TestClient, email: str = "jobs_user@example.com") -> dict:
    """Helper to register and login a user, returning Authorization header."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_job(
    db_session: Session,
    title: str = "Senior Distributed Systems Engineer",
    location: str = "San Francisco, CA",
    workplace_type: str = "REMOTE",
    employment_type: str = "FULL_TIME",
) -> Job:
    """Helper to create a Job with company and career source."""
    company = Company(name=f"Company-{uuid.uuid4().hex[:6]}", slug=f"co-{uuid.uuid4().hex[:6]}")
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        company_id=company.id,
        name="Career Portal",
        source_type="greenhouse",
        base_url=f"https://boards.greenhouse.io/{company.slug}",
    )
    db_session.add(source)
    db_session.commit()

    job = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"ext-{uuid.uuid4().hex[:8]}",
        title=title,
        description="<p>Build high-scale distributed backend systems in Python & Rust.</p>",
        location=location,
        workplace_type=workplace_type,
        employment_type=employment_type,
        application_url="https://example.com/apply/1",
        source_url="https://example.com/jobs/1",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_list_jobs_anonymous(client: TestClient, db_session: Session):
    """Verify anonymous job browsing with pagination and search."""
    job1 = _seed_job(db_session, title="Python Lead Developer", location="New York, NY")
    job2 = _seed_job(db_session, title="Frontend React Engineer", location="San Francisco, CA")

    # List all
    res = client.get("/api/v1/jobs?page=1&page_size=10")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    assert "page" in data
    assert "total_pages" in data

    # Search filter
    search_res = client.get("/api/v1/jobs?q=Python")
    assert search_res.status_code == status.HTTP_200_OK
    search_data = search_res.json()
    assert any(j["id"] == str(job1.id) for j in search_data["items"])
    assert not any(j["id"] == str(job2.id) for j in search_data["items"])


def test_job_detail_endpoint(client: TestClient, db_session: Session):
    """Verify detailed job view."""
    job = _seed_job(db_session, title="Platform Architect")

    res = client.get(f"/api/v1/jobs/{job.id}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["id"] == str(job.id)
    assert data["title"] == "Platform Architect"
    assert "description" in data
    assert "Build high-scale" in data["description"]
    assert data["is_saved"] is False


def test_save_and_unsave_job_lifecycle(client: TestClient, db_session: Session):
    """Verify bookmarking and removing bookmarks for a job."""
    email = "bookmark_user@example.com"
    headers = _get_auth_header(client, email)

    # Initialize profile
    client.get("/api/v1/profile", headers=headers)

    job = _seed_job(db_session, title="AI Research Engineer")

    # 1. Save job
    save_res = client.post(f"/api/v1/jobs/{job.id}/save", headers=headers)
    assert save_res.status_code == status.HTTP_200_OK
    assert save_res.json()["status"] == "saved"

    # 2. Check saved listing
    list_saved = client.get("/api/v1/jobs/saved", headers=headers)
    assert list_saved.status_code == status.HTTP_200_OK
    saved_data = list_saved.json()
    assert saved_data["total"] == 1
    assert saved_data["items"][0]["job"]["id"] == str(job.id)
    assert saved_data["items"][0]["job"]["is_saved"] is True

    # 3. Check job detail reflects is_saved = True
    detail_res = client.get(f"/api/v1/jobs/{job.id}", headers=headers)
    assert detail_res.status_code == status.HTTP_200_OK
    assert detail_res.json()["is_saved"] is True

    # 4. Unsave job
    unsave_res = client.delete(f"/api/v1/jobs/{job.id}/save", headers=headers)
    assert unsave_res.status_code == status.HTTP_200_OK
    assert unsave_res.json()["status"] == "unsaved"

    # 5. Check saved listing is now empty
    list_saved_after = client.get("/api/v1/jobs/saved", headers=headers)
    assert list_saved_after.json()["total"] == 0


def test_saved_jobs_requires_auth(client: TestClient, db_session: Session):
    """Verify unauthenticated requests to bookmark endpoints return 401."""
    job = _seed_job(db_session)
    res_list = client.get("/api/v1/jobs/saved")
    assert res_list.status_code == status.HTTP_401_UNAUTHORIZED

    res_save = client.post(f"/api/v1/jobs/{job.id}/save")
    assert res_save.status_code == status.HTTP_401_UNAUTHORIZED
