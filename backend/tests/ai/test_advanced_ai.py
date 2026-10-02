"""Phase 13: Advanced AI & Semantic Intelligence tests."""

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.cost.tracker import AICostTracker
from app.ai.ontology.service import SkillOntologyService
from app.ai.ranking.service import PersonalizedRankingService
from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_embedding import JobEmbedding
from app.models.job_requirements import JobRequirements
from app.models.skill import Skill
from app.models.user import User


# ============================================================================
# 1. SKILL ONTOLOGY & NORMALIZATION TESTS
# ============================================================================

def test_skill_ontology_normalization():
    service = SkillOntologyService()
    assert service.normalize_skill("js") == "JavaScript"
    assert service.normalize_skill("React.js") == "React"
    assert service.normalize_skill("k8s") == "Kubernetes"
    assert service.normalize_skill("postgres") == "PostgreSQL"
    assert service.normalize_skill("Golang") == "Go"
    assert service.normalize_skill("Unrecognized Custom Skill") == "Unrecognized Custom Skill"


def test_transferable_skills_detection():
    service = SkillOntologyService()
    
    # Candidate with Python and targets FastAPI & Rust
    transferable = service.find_transferable_skills(["Python"], ["FastAPI", "Rust"])
    targets = [t["target_skill"] for t in transferable]
    assert "FastAPI" in targets
    assert "Rust" not in targets


def test_skill_gap_analysis():
    service = SkillOntologyService()
    candidate_skills = ["Python"]
    required_skills = ["Python", "FastAPI", "Rust"]
    preferred_skills = ["AWS", "Redis"]

    gap_result = service.analyze_skill_gaps(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    assert "Python" in gap_result["matched_required"]
    assert "Rust" in gap_result["missing_required"]
    # FastAPI is linked to Python as transferable
    transferable_targets = [t["target_skill"] for t in gap_result["transferable_matches"]]
    assert "FastAPI" in transferable_targets
    assert gap_result["required_coverage"] > 0


# ============================================================================
# 2. AI COST & TELEMETRY TRACKER TESTS
# ============================================================================

def test_cost_tracker_metrics():
    tracker = AICostTracker()
    tracker.reset()

    tracker.record_usage(
        operation="job_extraction",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        latency_ms=120.0,
    )
    tracker.record_usage(
        operation="embedding_generation",
        model="text-embedding-3-small",
        prompt_tokens=2000,
        completion_tokens=0,
        latency_ms=45.0,
    )
    tracker.record_cache_hit(operation="job_extraction")
    tracker.record_cache_miss(operation="semantic_search")

    summary = tracker.get_summary()
    assert summary["total_calls"] == 2
    assert summary["total_tokens"] == 3500
    assert summary["total_estimated_cost_usd"] > 0
    assert summary["cache_hits"] == 1
    assert summary["cache_misses"] == 3
    assert summary["cache_hit_rate"] == 0.25


# ============================================================================
# 3. PERSONALIZED RANKING SERVICE TESTS
# ============================================================================

def test_personalized_ranking_boosts():
    service = PersonalizedRankingService()
    job_id = uuid.uuid4()

    mock_job = Job(
        id=job_id,
        title="Senior Python Backend Engineer",
        location="Remote",
        workplace_type="remote",
    )
    mock_profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        current_job_title="Python Engineer",
        years_of_experience=4.0,
    )

    # 1. Negative boost when user has already applied to this job
    boost_applied = service.compute_personalized_boost(
        job=mock_job,
        profile=mock_profile,
        saved_job_ids=set(),
        applied_job_ids={job_id},
    )
    assert boost_applied == -20.0

    # 2. Positive boost when bookmarked
    boost_saved = service.compute_personalized_boost(
        job=mock_job,
        profile=mock_profile,
        saved_job_ids={job_id},
        applied_job_ids=set(),
    )
    assert boost_saved >= 8.0


# ============================================================================
# 4. API ENDPOINT INTEGRATION TESTS
# ============================================================================

def _get_auth_header(client: TestClient, email: str = "adv_ai_user@example.com") -> dict:
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
def advanced_ai_seed(db_session: Session, client: TestClient):
    auth_header = _get_auth_header(client, "adv_candidate@example.com")
    user = db_session.query(User).filter_by(email="adv_candidate@example.com").first()

    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        first_name="Ada",
        last_name="Lovelace",
        headline="AI & Distributed Systems Engineer",
        years_of_experience=5.0,
    )
    db_session.add(profile)
    db_session.commit()

    py_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python")
    docker_skill = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker")
    db_session.add_all([py_skill, docker_skill])
    db_session.commit()

    db_session.add(CandidateSkill(id=uuid.uuid4(), profile_id=profile.id, skill_id=py_skill.id))
    db_session.add(CandidateSkill(id=uuid.uuid4(), profile_id=profile.id, skill_id=docker_skill.id))

    company = Company(id=uuid.uuid4(), name="Turing Labs", slug="turing-labs")
    source = CareerSource(id=uuid.uuid4(), company_id=company.id, name="Turing Careers", source_type="greenhouse", base_url="https://jobs.turing.ai")
    db_session.add_all([company, source])
    db_session.commit()

    job1 = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source.id,
        external_id="ext-adv-1",
        title="Senior Python Backend Developer",
        description="Looking for an experienced backend developer proficient with Python, FastAPI, and Kubernetes.",
        location="Remote",
        workplace_type="remote",
        employment_type="full-time",
        is_active=True,
    )
    db_session.add(job1)
    db_session.commit()

    reqs = JobRequirements(
        id=uuid.uuid4(),
        job_id=job1.id,
        minimum_experience_years=3.0,
        required_skills=["Python", "FastAPI", "Kubernetes"],
        preferred_skills=["AWS", "Redis"],
    )
    db_session.add(reqs)

    # Add a mock embedding for semantic search
    mock_vector = [0.05] * 1536
    embedding = JobEmbedding(
        id=uuid.uuid4(),
        job_id=job1.id,
        embedding=mock_vector,
        model="text-embedding-3-small",
        content_hash="mockhash123",
    )
    db_session.add(embedding)
    db_session.commit()

    return {
        "auth_header": auth_header,
        "job_id": str(job1.id),
        "user_id": str(user.id),
    }


def test_api_skill_gaps_endpoint(client: TestClient, advanced_ai_seed):
    auth_header = advanced_ai_seed["auth_header"]
    job_id = advanced_ai_seed["job_id"]

    res = client.get(f"/api/v1/ai/jobs/{job_id}/skill-gaps", headers=auth_header)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "matched_required" in data
    assert "missing_required" in data
    assert "transferable_matches" in data
    assert "Python" in data["matched_required"]


def test_api_similar_jobs_endpoint(client: TestClient, advanced_ai_seed):
    auth_header = advanced_ai_seed["auth_header"]
    job_id = advanced_ai_seed["job_id"]

    res = client.get(f"/api/v1/ai/jobs/{job_id}/similar", headers=auth_header)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert isinstance(data, list)


def test_api_semantic_search_endpoint(client: TestClient, advanced_ai_seed):
    auth_header = advanced_ai_seed["auth_header"]

    res = client.get("/api/v1/ai/jobs/search/semantic?query=Python+developer", headers=auth_header)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert isinstance(data, list)


def test_api_cost_telemetry_endpoint(client: TestClient, advanced_ai_seed):
    auth_header = advanced_ai_seed["auth_header"]

    res = client.get("/api/v1/ai/telemetry/cost", headers=auth_header)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "total_calls" in data
    assert "total_tokens" in data
    assert "cache_hit_rate" in data
