"""Integration tests for AI matching and extraction API endpoints."""

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_requirements import JobRequirements
from app.models.skill import Skill
from app.models.user import User


def _get_auth_header(client: TestClient, email: str = "ai_api_user@example.com") -> dict:
    """Helper to register and login a test user, returning auth header."""
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


@pytest.fixture
def api_test_data(db_session: Session, client: TestClient):
    """Seed user, candidate profile, skills, preferences, and a job with requirements."""
    auth_header = _get_auth_header(client, "candidate_ai_match@example.com")

    # Find the registered user
    user = db_session.query(User).filter_by(email="candidate_ai_match@example.com").first()

    # Create candidate profile
    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        first_name="Sam",
        last_name="Altman",
        headline="AI Engineering Lead",
        current_job_title="Senior AI Engineer",
        years_of_experience=6.0,
    )
    db_session.add(profile)
    db_session.commit()

    # Add skills
    py_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python")
    fastapi_skill = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi")
    db_session.add_all([py_skill, fastapi_skill])
    db_session.commit()

    cs1 = CandidateSkill(id=uuid.uuid4(), profile_id=profile.id, skill_id=py_skill.id, years_experience=5.0)
    cs2 = CandidateSkill(id=uuid.uuid4(), profile_id=profile.id, skill_id=fastapi_skill.id, years_experience=3.0)
    db_session.add_all([cs1, cs2])

    prefs = CandidatePreferences(
        id=uuid.uuid4(),
        profile_id=profile.id,
        workplace_types=["REMOTE"],
        employment_types=["FULL_TIME"],
        desired_titles=["Senior AI Engineer", "Staff Backend Engineer"],
    )
    db_session.add(prefs)
    db_session.commit()

    # Create Job
    company = Company(
        id=uuid.uuid4(),
        name="AI Endpoints Corp",
        slug=f"ai-endpoints-{uuid.uuid4().hex[:6]}",
        website_url="https://aiendpoints.example.com",
        is_active=True,
    )
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="AI Endpoints Board",
        source_type="greenhouse",
        base_url="https://aiendpoints.example.com/careers",
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()

    job = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"job-ai-{uuid.uuid4().hex[:6]}",
        title="Senior Python Backend Engineer",
        description="We need a Python engineer with FastAPI and cloud expertise to build backend services.",
        location="Remote",
        workplace_type="REMOTE",
        employment_type="FULL_TIME",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()

    reqs = JobRequirements(
        id=uuid.uuid4(),
        job_id=job.id,
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        minimum_experience_years=4.0,
    )
    db_session.add(reqs)
    db_session.commit()

    return auth_header, user, profile, job


def test_enhanced_match_endpoint_success(client: TestClient, api_test_data):
    """Verify POST /matching/jobs/{job_id}/enhanced returns deterministic, semantic, and hybrid scores."""
    auth_header, _, profile, job = api_test_data

    response = client.post(
        f"/api/v1/matching/jobs/{job.id}/enhanced",
        headers=auth_header,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["job_id"] == str(job.id)
    assert data["profile_id"] == str(profile.id)
    assert "deterministic_score" in data
    assert data["deterministic_score"] > 0
    assert "hybrid_score" in data
    assert "ai_status" in data
    assert data["ai_status"] in ["AI_AVAILABLE", "AI_PARTIAL", "DISABLED"]

    # Verify narrative explanation is present and structured
    assert "explanation" in data
    explanation = data["explanation"]
    assert "summary" in explanation
    assert "strengths" in explanation
    assert "recommendation" in explanation


def test_enhanced_match_unauthenticated(client: TestClient, api_test_data):
    """Verify unauthenticated call to enhanced match returns 401."""
    _, _, _, job = api_test_data

    response = client.post(f"/api/v1/matching/jobs/{job.id}/enhanced")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_enhanced_match_job_not_found(client: TestClient, api_test_data):
    """Verify nonexistent job ID returns 404."""
    auth_header, _, _, _ = api_test_data
    fake_id = uuid.uuid4()

    response = client.post(
        f"/api/v1/matching/jobs/{fake_id}/enhanced",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Job not found" in response.json()["detail"]


def test_ai_job_extraction_endpoints(client: TestClient, api_test_data):
    """Verify POST /ai/jobs/{job_id}/extract and GET /ai/jobs/{job_id}/extraction."""
    auth_header, _, _, job = api_test_data

    # 1. Trigger extraction
    extract_res = client.post(
        f"/api/v1/ai/jobs/{job.id}/extract",
        headers=auth_header,
    )
    assert extract_res.status_code == status.HTTP_200_OK
    data = extract_res.json()
    assert data["job_id"] == str(job.id)
    assert data["is_success"] is True
    assert data["structured_requirements"] is not None
    assert "Python" in data["structured_requirements"]["required_skills"]

    # 2. Retrieve extraction from cache
    get_res = client.get(
        f"/api/v1/ai/jobs/{job.id}/extraction",
        headers=auth_header,
    )
    assert get_res.status_code == status.HTTP_200_OK
    cached_data = get_res.json()
    assert cached_data["input_hash"] == data["input_hash"]

    # 3. Nonexistent job extraction returns 404
    nonexistent_id = uuid.uuid4()
    not_found_res = client.get(
        f"/api/v1/ai/jobs/{nonexistent_id}/extraction",
        headers=auth_header,
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
