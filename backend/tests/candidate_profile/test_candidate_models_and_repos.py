"""Database model and repository tests verifying relational constraints and cascade integrity."""

from datetime import date
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.education import Education
from app.models.enums import ProficiencyLevel
from app.models.experience import Experience
from app.models.skill import Skill
from app.models.user import User
from app.repositories.candidate_preferences import CandidatePreferencesRepository
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.candidate_skill import CandidateSkillRepository
from app.repositories.education import EducationRepository
from app.repositories.experience import ExperienceRepository
from app.repositories.skill import SkillRepository
from app.repositories.user import UserRepository
from app.schemas.candidate_profile import CandidateProfileCreate
from app.schemas.education import EducationCreate
from app.schemas.experience import ExperienceCreate


def test_user_email_unique_constraint(db_session: Session):
    """Verify that duplicate user emails violate the unique constraint."""
    user_repo = UserRepository(db_session)
    email = "test@example.com"
    user_repo.create(email=email, password_hash="hash1")

    with pytest.raises(IntegrityError):
        user_repo.create(email=email, password_hash="hash2")
    db_session.rollback()


def test_candidate_profile_user_unique_constraint(db_session: Session):
    """Verify that a user can have at most one CandidateProfile."""
    user = User(email="oneprofile@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    profile1 = CandidateProfile(user_id=user.id, first_name="Alex")
    db_session.add(profile1)
    db_session.commit()

    profile2 = CandidateProfile(user_id=user.id, first_name="Duplicate")
    db_session.add(profile2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_skill_normalized_name_unique_constraint(db_session: Session):
    """Verify that canonical skills enforce uniqueness on normalized_name."""
    skill_repo = SkillRepository(db_session)
    skill_repo.get_or_create("FastAPI")

    # Second get_or_create returns existing
    skill2 = skill_repo.get_or_create("  fastapi  ")
    assert skill2.normalized_name == "fastapi"

    # Direct insert with duplicate normalized name fails
    dup_skill = Skill(name="FastAPI 2", normalized_name="fastapi")
    db_session.add(dup_skill)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_candidate_skill_profile_unique_constraint(db_session: Session):
    """Verify that attaching the same skill twice to a profile violates composite unique constraint."""
    user = User(email="skills@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    profile = CandidateProfile(user_id=user.id)
    skill = Skill(name="PostgreSQL", normalized_name="postgresql")
    db_session.add_all([profile, skill])
    db_session.commit()

    cs1 = CandidateSkill(profile_id=profile.id, skill_id=skill.id, proficiency="ADVANCED")
    db_session.add(cs1)
    db_session.commit()

    cs2 = CandidateSkill(profile_id=profile.id, skill_id=skill.id, proficiency="EXPERT")
    db_session.add(cs2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_user_removes_profile_and_children(db_session: Session):
    """Verify that deleting a User cascades to delete CandidateProfile, skills, experiences, etc."""
    user = User(email="cascade@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()

    profile_repo = CandidateProfileRepository(db_session)
    profile = profile_repo.create(
        user.id, CandidateProfileCreate(first_name="Sam", last_name="Altman")
    )

    skill = Skill(name="Docker", normalized_name="docker")
    db_session.add(skill)
    db_session.commit()

    cs_repo = CandidateSkillRepository(db_session)
    cs_repo.create(profile.id, skill.id, proficiency=ProficiencyLevel.ADVANCED.value)

    exp_repo = ExperienceRepository(db_session)
    exp_repo.create(
        profile.id,
        ExperienceCreate(
            company_name="OpenAI",
            job_title="CEO",
            start_date=date(2019, 1, 1),
            is_current=True,
        ),
    )

    edu_repo = EducationRepository(db_session)
    edu_repo.create(
        profile.id,
        EducationCreate(
            institution_name="Stanford",
            degree="Dropout",
        ),
    )

    # Delete User
    db_session.delete(user)
    db_session.commit()

    # Verify cascading deletes
    assert db_session.get(CandidateProfile, profile.id) is None
    assert len(cs_repo.list_for_profile(profile.id)) == 0
    assert len(exp_repo.list_for_profile(profile.id)) == 0
    assert len(edu_repo.list_for_profile(profile.id)) == 0
    # Canonical skill itself should still exist
    assert db_session.get(Skill, skill.id) is not None
