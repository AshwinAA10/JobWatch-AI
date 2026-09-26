"""Unit tests for deterministic profile completeness calculations."""

import uuid
from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.education import Education
from app.models.experience import Experience
from app.models.skill import Skill
from app.services.profile_completeness import ProfileCompletenessService


def test_empty_profile_completeness():
    """Verify that an empty profile yields 0% completeness with all sections missing."""
    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    score, missing, breakdown = ProfileCompletenessService.calculate(profile)

    assert score == 0
    assert set(missing) == {
        "basic_identity",
        "headline",
        "bio",
        "skills",
        "experience",
        "education",
        "preferences",
    }
    assert all(status is False for status in breakdown.values())


def test_incremental_profile_completeness():
    """Verify that adding sections deterministically increases completeness according to weights."""
    profile = CandidateProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )

    # 1. Add Basic Identity (15%)
    profile.first_name = "Jane"
    profile.last_name = "Doe"
    profile.city = "San Francisco"
    score, missing, _ = ProfileCompletenessService.calculate(profile)
    assert score == 15
    assert "basic_identity" not in missing

    # 2. Add Headline (10% -> 25%)
    profile.headline = "Staff Backend Engineer"
    score, missing, _ = ProfileCompletenessService.calculate(profile)
    assert score == 25
    assert "headline" not in missing

    # 3. Add Bio (10% -> 35%)
    profile.bio = "Experienced distributed systems architect with 10+ years."
    score, missing, _ = ProfileCompletenessService.calculate(profile)
    assert score == 35
    assert "bio" not in missing

    # 4. Add Skills (20% -> 55%)
    dummy_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python")
    candidate_skill = CandidateSkill(
        id=uuid.uuid4(),
        profile_id=profile.id,
        skill_id=dummy_skill.id,
        skill=dummy_skill,
        proficiency="EXPERT",
    )
    profile.skills = [candidate_skill]
    score, missing, _ = ProfileCompletenessService.calculate(profile)
    assert score == 55
    assert "skills" not in missing

    # 5. Add Experience (20% -> 75%)
    dummy_exp = Experience(
        id=uuid.uuid4(),
        profile_id=profile.id,
        company_name="Acme Corp",
        job_title="Senior Engineer",
    )
    profile.experiences = [dummy_exp]
    score, missing, _ = ProfileCompletenessService.calculate(profile)
    assert score == 75
    assert "experience" not in missing

    # 6. Add Education (10% -> 85%)
    dummy_edu = Education(
        id=uuid.uuid4(),
        profile_id=profile.id,
        institution_name="Stanford University",
        degree="B.S. Computer Science",
    )
    profile.educations = [dummy_edu]
    score, missing, _ = ProfileCompletenessService.calculate(profile)
    assert score == 85
    assert "education" not in missing

    # 7. Add Preferences (15% -> 100%)
    prefs = CandidatePreferences(
        id=uuid.uuid4(),
        profile_id=profile.id,
        desired_titles=["Staff Engineer", "Principal Engineer"],
        preferred_locations=["Remote", "San Francisco, CA"],
    )
    profile.preferences = prefs
    score, missing, breakdown = ProfileCompletenessService.calculate(profile)
    assert score == 100
    assert len(missing) == 0
    assert all(status is True for status in breakdown.values())
