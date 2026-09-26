"""Candidate profile, skills, experience, education, and preferences endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.candidate_preferences import (
    CandidatePreferencesResponse,
    CandidatePreferencesUpdate,
)
from app.schemas.candidate_profile import (
    CandidateProfileCreate,
    CandidateProfileDetailResponse,
    CandidateProfileResponse,
    CandidateProfileUpdate,
    ProfileCompletenessResponse,
)
from app.schemas.education import (
    EducationCreate,
    EducationResponse,
    EducationUpdate,
)
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
)
from app.schemas.skill import (
    CandidateSkillCreate,
    CandidateSkillResponse,
    CandidateSkillUpdate,
)
from app.services.exceptions import (
    DuplicateSkillError,
    ProfileNotFoundError,
    ResourceNotFoundError,
    UnauthorizedAccessError,
)
from app.services.profile import ProfileService

router = APIRouter()


# --- Core Candidate Profile Endpoints ---


@router.get(
    "",
    response_model=CandidateProfileDetailResponse,
    summary="Get Current User Candidate Profile",
    description="Fetches the candidate profile with nested skills, experience, education, and preferences.",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfileDetailResponse:
    """Retrieve full candidate profile for the authenticated user."""
    service = ProfileService(db)
    profile = service.get_or_create_profile(current_user.id)
    return CandidateProfileDetailResponse.model_validate(profile)


@router.post(
    "",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Candidate Profile",
    description="Explicitly initializes a candidate profile for the current user.",
)
def create_my_profile(
    profile_in: CandidateProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    """Initialize a candidate profile for current user."""
    service = ProfileService(db)
    profile = service.get_or_create_profile(current_user.id, profile_in)
    return CandidateProfileResponse.model_validate(profile)


@router.put(
    "",
    response_model=CandidateProfileDetailResponse,
    summary="Update Candidate Profile",
    description="Updates candidate profile attributes and refreshes completeness score.",
)
def update_my_profile(
    profile_in: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateProfileDetailResponse:
    """Update profile information."""
    service = ProfileService(db)
    profile = service.update_profile(current_user.id, profile_in)
    return CandidateProfileDetailResponse.model_validate(profile)


@router.get(
    "/completeness",
    response_model=ProfileCompletenessResponse,
    summary="Get Profile Completeness Breakdown",
    description="Returns deterministic completeness percentage, missing sections, and checklist.",
)
def get_profile_completeness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileCompletenessResponse:
    """Get candidate profile completeness score and breakdown."""
    service = ProfileService(db)
    return service.get_completeness(current_user.id)


# --- Skills Endpoints ---


@router.get(
    "/skills",
    response_model=List[CandidateSkillResponse],
    summary="List Candidate Skills",
    description="Lists all skills associated with the authenticated user's profile.",
)
def list_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CandidateSkillResponse]:
    """List skills for current profile."""
    service = ProfileService(db)
    profile = service.get_or_create_profile(current_user.id)
    return [
        CandidateSkillResponse.model_validate(s)
        for s in service.candidate_skill_repo.list_for_profile(profile.id)
    ]


@router.post(
    "/skills",
    response_model=CandidateSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attach Skill to Profile",
    description="Attaches a skill to the profile by name or skill ID, specifying proficiency and experience.",
)
def add_skill(
    skill_in: CandidateSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateSkillResponse:
    """Attach skill to profile."""
    service = ProfileService(db)
    try:
        assoc = service.add_skill(current_user.id, skill_in)
        return CandidateSkillResponse.model_validate(assoc)
    except DuplicateSkillError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put(
    "/skills/{skill_assoc_id}",
    response_model=CandidateSkillResponse,
    summary="Update Attached Skill",
    description="Updates proficiency or years of experience for an attached skill.",
)
def update_skill(
    skill_assoc_id: UUID,
    update_in: CandidateSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateSkillResponse:
    """Update attached skill details."""
    service = ProfileService(db)
    try:
        assoc = service.update_skill(current_user.id, skill_assoc_id, update_in)
        return CandidateSkillResponse.model_validate(assoc)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete(
    "/skills/{skill_assoc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Skill from Profile",
    description="Detaches a skill from the profile.",
)
def delete_skill(
    skill_assoc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Remove attached skill."""
    service = ProfileService(db)
    try:
        service.remove_skill(current_user.id, skill_assoc_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# --- Experience Endpoints ---


@router.get(
    "/experience",
    response_model=List[ExperienceResponse],
    summary="List Work Experiences",
    description="Lists work experience history for current user sorted chronologically.",
)
def list_experience(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ExperienceResponse]:
    """List work experience entries."""
    service = ProfileService(db)
    profile = service.get_or_create_profile(current_user.id)
    return [
        ExperienceResponse.model_validate(e)
        for e in service.exp_repo.list_for_profile(profile.id)
    ]


@router.post(
    "/experience",
    response_model=ExperienceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Work Experience",
    description="Adds a new work experience record to the profile.",
)
def add_experience(
    exp_in: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExperienceResponse:
    """Create work experience entry."""
    service = ProfileService(db)
    exp = service.add_experience(current_user.id, exp_in)
    return ExperienceResponse.model_validate(exp)


@router.put(
    "/experience/{exp_id}",
    response_model=ExperienceResponse,
    summary="Update Work Experience",
    description="Updates an existing work experience record.",
)
def update_experience(
    exp_id: UUID,
    exp_in: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExperienceResponse:
    """Update work experience entry."""
    service = ProfileService(db)
    try:
        exp = service.update_experience(current_user.id, exp_id, exp_in)
        return ExperienceResponse.model_validate(exp)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete(
    "/experience/{exp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Work Experience",
    description="Removes a work experience record from the profile.",
)
def delete_experience(
    exp_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete work experience entry."""
    service = ProfileService(db)
    try:
        service.remove_experience(current_user.id, exp_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# --- Education Endpoints ---


@router.get(
    "/education",
    response_model=List[EducationResponse],
    summary="List Education History",
    description="Lists academic history records for current user sorted chronologically.",
)
def list_education(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[EducationResponse]:
    """List education entries."""
    service = ProfileService(db)
    profile = service.get_or_create_profile(current_user.id)
    return [
        EducationResponse.model_validate(e)
        for e in service.edu_repo.list_for_profile(profile.id)
    ]


@router.post(
    "/education",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Education Entry",
    description="Adds a new academic credential to the profile.",
)
def add_education(
    edu_in: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EducationResponse:
    """Create education entry."""
    service = ProfileService(db)
    edu = service.add_education(current_user.id, edu_in)
    return EducationResponse.model_validate(edu)


@router.put(
    "/education/{edu_id}",
    response_model=EducationResponse,
    summary="Update Education Entry",
    description="Updates an existing education record.",
)
def update_education(
    edu_id: UUID,
    edu_in: EducationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EducationResponse:
    """Update education entry."""
    service = ProfileService(db)
    try:
        edu = service.update_education(current_user.id, edu_id, edu_in)
        return EducationResponse.model_validate(edu)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete(
    "/education/{edu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Education Entry",
    description="Removes an education record from the profile.",
)
def delete_education(
    edu_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete education entry."""
    service = ProfileService(db)
    try:
        service.remove_education(current_user.id, edu_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UnauthorizedAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# --- Preferences Endpoints ---


@router.get(
    "/preferences",
    response_model=CandidatePreferencesResponse,
    summary="Get Job Preferences",
    description="Fetches candidate target job criteria and compensation expectations.",
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidatePreferencesResponse:
    """Get candidate preferences."""
    service = ProfileService(db)
    prefs = service.get_preferences(current_user.id)
    return CandidatePreferencesResponse.model_validate(prefs)


@router.put(
    "/preferences",
    response_model=CandidatePreferencesResponse,
    summary="Update Job Preferences",
    description="Updates candidate target job criteria, locations, workplace types, and salary expectations.",
)
def update_preferences(
    prefs_in: CandidatePreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidatePreferencesResponse:
    """Update candidate preferences."""
    service = ProfileService(db)
    prefs = service.update_preferences(current_user.id, prefs_in)
    return CandidatePreferencesResponse.model_validate(prefs)
