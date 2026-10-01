"""Tests for vector embeddings generation, PII minimization, caching, and cosine similarity."""

import uuid
import pytest
from sqlalchemy.orm import Session

from app.ai.embeddings.models import (
    build_candidate_embedding_text,
    build_job_embedding_text,
)
from app.ai.embeddings.service import EmbeddingService
from app.ai.providers.fake_provider import FakeProvider
from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_requirements import JobRequirements
from app.models.skill import Skill
from app.models.user import User


@pytest.fixture
def test_candidate(db_session: Session) -> CandidateProfile:
    """Create a candidate user, profile, skills, and preferences."""
    user = User(
        id=uuid.uuid4(),
        email=f"ai_candidate_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="secret_password_hash_123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        first_name="Jane",
        last_name="Doe",
        headline="Senior AI Systems Architect",
        current_job_title="Lead AI Engineer",
        years_of_experience=8.0,
        highest_education_level="Master's Degree",
    )
    db_session.add(profile)
    db_session.commit()

    python_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python")
    docker_skill = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker")
    db_session.add_all([python_skill, docker_skill])
    db_session.commit()

    cand_skill1 = CandidateSkill(
        id=uuid.uuid4(),
        profile_id=profile.id,
        skill_id=python_skill.id,
        years_experience=6.0,
    )
    cand_skill2 = CandidateSkill(
        id=uuid.uuid4(),
        profile_id=profile.id,
        skill_id=docker_skill.id,
        years_experience=4.0,
    )
    db_session.add_all([cand_skill1, cand_skill2])

    prefs = CandidatePreferences(
        id=uuid.uuid4(),
        profile_id=profile.id,
        workplace_types=["REMOTE", "HYBRID"],
        employment_types=["FULL_TIME"],
        desired_titles=["Senior AI Engineer", "Staff ML Engineer"],
        preferred_locations=["San Francisco", "Remote"],
    )
    db_session.add(prefs)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@pytest.fixture
def test_job(db_session: Session) -> Job:
    """Create a test job with requirements."""
    company = Company(
        id=uuid.uuid4(),
        name="Vector AI Inc",
        slug=f"vector-ai-{uuid.uuid4().hex[:6]}",
        website_url="https://vectorai.example.com",
        is_active=True,
    )
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Vector Careers",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/vectorai",
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()

    job = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"vector-job-{uuid.uuid4().hex[:6]}",
        title="Lead Machine Learning Engineer",
        description="Looking for an ML engineer skilled in Python, PyTorch, and distributed training systems.",
        location="Remote",
        employment_type="FULL_TIME",
        workplace_type="REMOTE",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()

    reqs = JobRequirements(
        id=uuid.uuid4(),
        job_id=job.id,
        required_skills=["Python", "PyTorch"],
        preferred_skills=["Docker", "Kubernetes"],
        minimum_experience_years=5.0,
    )
    db_session.add(reqs)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_pii_minimization_in_candidate_text(test_candidate: CandidateProfile):
    """Verify candidate embedding text excludes PII (email, passwords, tokens, full name)."""
    text = build_candidate_embedding_text(test_candidate)

    # Strictly no private credentials or sensitive user data
    assert "secret_password_hash_123" not in text
    assert "ai_candidate_test@example.com" not in text
    assert str(test_candidate.user_id) not in text
    assert str(test_candidate.id) not in text

    # Includes relevant matching information
    assert "Title: Lead AI Engineer" in text
    assert "Skills: Docker, Python" in text
    assert "Experience: 8.0 years" in text
    assert "Workplace: HYBRID, REMOTE" in text
    assert "Target Roles: Senior AI Engineer, Staff ML Engineer" in text


def test_job_embedding_text_builder(test_job: Job):
    """Verify job embedding text representation builds deterministically."""
    text = build_job_embedding_text(test_job)

    assert "Role: Lead Machine Learning Engineer" in text
    assert "Workplace: REMOTE" in text
    assert "Required Skills: PyTorch, Python" in text
    assert "Description:" in text


def test_cosine_similarity_edge_cases():
    """Verify cosine similarity calculation with exact mathematical properties."""
    calc = EmbeddingService.calculate_cosine_similarity

    # 1. Identical unit vectors -> 1.0
    vec_a = [1.0, 0.0, 0.0]
    assert abs(calc(vec_a, vec_a) - 1.0) < 1e-6

    # 2. Orthogonal unit vectors -> 0.0
    vec_b = [0.0, 1.0, 0.0]
    assert abs(calc(vec_a, vec_b) - 0.0) < 1e-6

    # 3. Opposite vectors -> clamped to 0.0
    vec_c = [-1.0, 0.0, 0.0]
    assert calc(vec_a, vec_c) == 0.0

    # 4. Zero vector -> 0.0
    assert calc([0.0, 0.0], [1.0, 1.0]) == 0.0

    # 5. Empty or length mismatch -> 0.0
    assert calc([], [1.0]) == 0.0
    assert calc([1.0], [1.0, 2.0]) == 0.0


def test_candidate_embedding_caching_and_invalidation(
    db_session: Session,
    test_candidate: CandidateProfile,
):
    """Verify candidate vector is cached and invalidated only on profile changes."""
    provider = FakeProvider(dimensions=1536)
    service = EmbeddingService(db=db_session, embedding_provider=provider)

    # 1. First generation -> provider called once
    vec1 = service.get_or_create_candidate_embedding(test_candidate)
    assert vec1 is not None
    assert len(vec1) == 1536
    assert provider.call_count_embed == 1

    # 2. Subsequent call -> cache hit
    vec2 = service.get_or_create_candidate_embedding(test_candidate)
    assert vec2 is not None
    assert provider.call_count_embed == 1
    assert vec1 == vec2

    # 3. Material profile change -> invalidation & regeneration
    test_candidate.current_job_title = "Principal Distributed Systems Architect"
    db_session.add(test_candidate)
    db_session.commit()

    vec3 = service.get_or_create_candidate_embedding(test_candidate)
    assert vec3 is not None
    assert provider.call_count_embed == 2


def test_job_embedding_caching_and_invalidation(
    db_session: Session,
    test_job: Job,
):
    """Verify job vector is cached and invalidated only when job details change."""
    provider = FakeProvider(dimensions=1536)
    service = EmbeddingService(db=db_session, embedding_provider=provider)

    # 1. First generation
    vec1 = service.get_or_create_job_embedding(test_job)
    assert vec1 is not None
    assert provider.call_count_embed == 1

    # 2. Subsequent call -> cached
    vec2 = service.get_or_create_job_embedding(test_job)
    assert vec2 is not None
    assert provider.call_count_embed == 1

    # 3. Job title change -> regeneration
    test_job.title = "Director of Machine Learning"
    db_session.add(test_job)
    db_session.commit()

    vec3 = service.get_or_create_job_embedding(test_job)
    assert vec3 is not None
    assert provider.call_count_embed == 2


def test_embedding_service_provider_failure_graceful(
    db_session: Session,
    test_candidate: CandidateProfile,
):
    """Verify provider failures do not crash the service and return None."""
    fail_provider = FakeProvider(should_fail=True, failure_type="generic")
    service = EmbeddingService(db=db_session, embedding_provider=fail_provider)

    result = service.get_or_create_candidate_embedding(test_candidate)
    assert result is None
