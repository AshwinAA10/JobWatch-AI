"""Integration tests for matching API endpoints, authentication, isolation, and persistence."""

from datetime import datetime, timezone
import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job


def _get_auth_header(client: TestClient, email: str = "matching_user@example.com") -> dict:
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


def _seed_test_job(db: Session, title: str = "Full Stack Engineer", location: str = "Coimbatore") -> Job:
    """Seed a test job opening for matching integration tests."""
    company = Company(
        id=uuid.uuid4(),
        name=f"Match Corp {uuid.uuid4().hex[:6]}",
        slug=f"match-corp-{uuid.uuid4().hex[:8]}",
        website_url="https://matchcorp.example.com",
    )
    db.add(company)
    db.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Match Board",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/matchcorp",
        is_active=True,
    )
    db.add(source)
    db.commit()

    job = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"ext-{uuid.uuid4().hex[:8]}",
        title=title,
        location=location,
        workplace_type="REMOTE",
        employment_type="FULL_TIME",
        is_active=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_matching_requires_authentication(client: TestClient):
    """Endpoint rejects unauthenticated requests."""
    fake_id = uuid.uuid4()
    res = client.post(f"/api/v1/matching/jobs/{fake_id}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_matching_job_not_found(client: TestClient):
    """Returns 404 when matching against nonexistent job ID."""
    headers = _get_auth_header(client, "missing_job_user@example.com")
    # Initialize profile first
    client.get("/api/v1/profile", headers=headers)

    fake_id = uuid.uuid4()
    res = client.post(f"/api/v1/matching/jobs/{fake_id}", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert "Job not found" in res.json()["detail"]


def test_job_requirements_endpoints(client: TestClient, db_session: Session):
    """Set and retrieve structured requirements for a job."""
    headers = _get_auth_header(client, "req_admin@example.com")
    job = _seed_test_job(db_session, title="Backend Engineer")

    # Set requirements
    payload = {
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["PostgreSQL", "Docker"],
        "minimum_experience_years": 3.0,
        "maximum_experience_years": 6.0,
        "minimum_salary": 90000,
        "maximum_salary": 120000,
        "salary_currency": "USD",
        "required_education_level": "Bachelor's",
    }
    put_res = client.put(f"/api/v1/matching/jobs/{job.id}/requirements", json=payload, headers=headers)
    assert put_res.status_code == status.HTTP_200_OK
    data = put_res.json()
    assert data["job_id"] == str(job.id)
    assert data["required_skills"] == ["Python", "FastAPI"]
    assert data["minimum_experience_years"] == 3.0

    # Get requirements
    get_res = client.get(f"/api/v1/matching/jobs/{job.id}/requirements", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["salary_currency"] == "USD"


def test_matching_flow_and_persistence(client: TestClient, db_session: Session):
    """Full end-to-end matching flow with profile, requirements, calculation, and retrieval."""
    headers = _get_auth_header(client, "match_candidate@example.com")
    # 1. Initialize candidate profile
    client.get("/api/v1/profile", headers=headers)
    client.put(
        "/api/v1/profile",
        json={"years_of_experience": 4.0, "highest_education_level": "Bachelor's Degree"},
        headers=headers,
    )
    # Add skills
    client.post("/api/v1/profile/skills", json={"skill_name": "React", "proficiency": "ADVANCED"}, headers=headers)
    client.post("/api/v1/profile/skills", json={"skill_name": "TypeScript", "proficiency": "ADVANCED"}, headers=headers)
    # Set preferences
    client.put(
        "/api/v1/profile/preferences",
        json={
            "desired_titles": ["Software Engineer"],
            "workplace_types": ["REMOTE"],
            "employment_types": ["FULL_TIME"],
            "minimum_salary": 90000,
            "maximum_salary": 130000,
            "salary_currency": "USD",
        },
        headers=headers,
    )

    # 2. Seed Job and Requirements
    job = _seed_test_job(db_session, title="Senior Software Developer", location="Coimbatore")
    req_payload = {
        "required_skills": ["React", "TypeScript"],
        "preferred_skills": ["NodeJS"],
        "minimum_experience_years": 3.0,
        "minimum_salary": 95000,
        "maximum_salary": 140000,
        "salary_currency": "USD",
        "required_education_level": "Bachelor's",
    }
    client.put(f"/api/v1/matching/jobs/{job.id}/requirements", json=req_payload, headers=headers)

    # 3. Evaluate Match (POST)
    match_res = client.post(f"/api/v1/matching/jobs/{job.id}", headers=headers)
    assert match_res.status_code == status.HTTP_200_OK
    match_data = match_res.json()

    assert match_data["score"] >= 80.0
    assert match_data["scoring_version"] == "v1"
    assert "skills" in match_data["breakdown"]
    assert match_data["breakdown"]["skills"]["status"] in ["MATCH", "PARTIAL"]
    assert len(match_data["reasons"]) > 0

    # 4. Fetch Persisted Match (GET)
    get_match_res = client.get(f"/api/v1/matching/jobs/{job.id}", headers=headers)
    assert get_match_res.status_code == status.HTTP_200_OK
    assert get_match_res.json()["score"] == match_data["score"]

    # 5. List Matches for User
    list_res = client.get("/api/v1/matching/matches?min_score=50", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    matches = list_res.json()
    assert len(matches) >= 1
    assert matches[0]["job_id"] == str(job.id)


def test_matching_profile_isolation(client: TestClient, db_session: Session):
    """User B cannot see User A's calculated match result."""
    user_a_headers = _get_auth_header(client, "user_a@example.com")
    user_b_headers = _get_auth_header(client, "user_b@example.com")

    # Initialize profiles
    client.get("/api/v1/profile", headers=user_a_headers)
    client.get("/api/v1/profile", headers=user_b_headers)

    job = _seed_test_job(db_session, title="DevOps Engineer")

    # User A matches job
    res_a = client.post(f"/api/v1/matching/jobs/{job.id}", headers=user_a_headers)
    assert res_a.status_code == status.HTTP_200_OK

    # User B tries to fetch match for that job before computing it -> 404
    res_b = client.get(f"/api/v1/matching/jobs/{job.id}", headers=user_b_headers)
    assert res_b.status_code == status.HTTP_404_NOT_FOUND
