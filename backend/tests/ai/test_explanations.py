"""Tests for AI explanation generation, caching, and deterministic fallback."""

import uuid
import pytest
from sqlalchemy.orm import Session

from app.ai.explanations.generator import AIExplanationGenerator
from app.ai.explanations.prompts import AIExplanationSchema, build_explanation_payload
from app.ai.providers.fake_provider import FakeProvider
from app.models.candidate_profile import CandidateProfile
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.user import User


@pytest.fixture
def test_data(db_session: Session):
    """Seed user, profile, company, and job."""
    user = User(
        id=uuid.uuid4(),
        email=f"exp_user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="secret_hash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        first_name="Alice",
        last_name="Smith",
    )
    db_session.add(profile)
    db_session.commit()

    company = Company(
        id=uuid.uuid4(),
        name="Explanations Inc",
        slug=f"exp-inc-{uuid.uuid4().hex[:6]}",
        website_url="https://exp.example.com",
        is_active=True,
    )
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="Exp Board",
        source_type="greenhouse",
        base_url="https://exp.example.com/careers",
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()

    job = Job(
        id=uuid.uuid4(),
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"exp-job-{uuid.uuid4().hex[:6]}",
        title="Staff Backend Engineer",
        description="Looking for an experienced engineer in Python and distributed systems.",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()

    return profile, job


def test_build_explanation_payload_structure():
    """Verify explanation payload includes structured match data and forbids score alteration."""
    payload = build_explanation_payload(
        job_title="Staff Backend Engineer",
        deterministic_score=85.0,
        semantic_score=80.0,
        hybrid_score=83.5,
        matched_criteria=["Python", "FastAPI", "Distributed Systems"],
        missing_criteria=["Kubernetes"],
        mismatches=[],
        deterministic_reasons=["5+ years experience required; candidate has 8 years."],
    )

    assert "Staff Backend Engineer" in payload
    assert "85.0" in payload
    assert "80.0" in payload
    assert "83.5" in payload
    assert "Python" in payload
    assert "Kubernetes" in payload


def test_ai_explanation_generator_happy_path(db_session: Session, test_data):
    """Verify narrative explanation generation with caching in DB."""
    profile, job = test_data

    provider = FakeProvider(
        structured_override=AIExplanationSchema(
            summary="Candidate is an exceptional match with deep expertise in Python and FastAPI.",
            strengths=["Strong core backend engineering", "Exceeds minimum experience requirement"],
            gaps=["Lacks explicit mention of Kubernetes in verified skills"],
            recommendation="Strongly recommended to apply, highlighting container orchestration projects.",
        )
    )

    generator = AIExplanationGenerator(db=db_session, llm_provider=provider)

    # 1. First call -> calls provider
    explanation = generator.generate_explanation(
        profile_id=profile.id,
        job_id=job.id,
        job_title=job.title,
        deterministic_score=85.0,
        semantic_score=80.0,
        hybrid_score=83.5,
        matched_criteria=["Python", "FastAPI"],
        missing_criteria=["Kubernetes"],
        mismatches=[],
        deterministic_reasons=["Experience satisfied."],
        ai_enabled=True,
    )

    assert explanation is not None
    assert "exceptional match" in explanation.summary
    assert len(explanation.strengths) == 2
    assert provider.call_count_structured == 1

    # 2. Second call with identical input -> cache hit
    explanation_cached = generator.generate_explanation(
        profile_id=profile.id,
        job_id=job.id,
        job_title=job.title,
        deterministic_score=85.0,
        semantic_score=80.0,
        hybrid_score=83.5,
        matched_criteria=["Python", "FastAPI"],
        missing_criteria=["Kubernetes"],
        mismatches=[],
        deterministic_reasons=["Experience satisfied."],
        ai_enabled=True,
    )

    assert explanation_cached.summary == explanation.summary
    assert provider.call_count_structured == 1  # No extra LLM call


def test_ai_explanation_deterministic_fallback_on_failure(db_session: Session, test_data):
    """Verify generator falls back to rule-based explanation when provider throws exception."""
    profile, job = test_data
    fail_provider = FakeProvider(should_fail=True, failure_type="generic")
    generator = AIExplanationGenerator(db=db_session, llm_provider=fail_provider)

    explanation = generator.generate_explanation(
        profile_id=profile.id,
        job_id=job.id,
        job_title=job.title,
        deterministic_score=78.0,
        semantic_score=None,
        hybrid_score=78.0,
        matched_criteria=["AWS", "Terraform"],
        missing_criteria=["Ansible"],
        mismatches=[],
        deterministic_reasons=["Workplace matches."],
        ai_enabled=True,
    )

    # Successfully returns fallback explanation
    assert explanation is not None
    assert "scored 78/100 on deterministic rules" in explanation.summary
    assert "AWS" in explanation.strengths


def test_ai_explanation_disabled_flag(db_session: Session, test_data):
    """Verify generator returns deterministic fallback when ai_enabled=False without calling LLM."""
    profile, job = test_data
    provider = FakeProvider()
    generator = AIExplanationGenerator(db=db_session, llm_provider=provider)

    explanation = generator.generate_explanation(
        profile_id=profile.id,
        job_id=job.id,
        job_title=job.title,
        deterministic_score=90.0,
        semantic_score=90.0,
        hybrid_score=90.0,
        matched_criteria=["React", "TypeScript"],
        missing_criteria=[],
        mismatches=[],
        deterministic_reasons=[],
        ai_enabled=False,
    )

    assert explanation is not None
    assert "scored 90/100" in explanation.summary
    assert provider.call_count_structured == 0
