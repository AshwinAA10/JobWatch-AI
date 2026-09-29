"""Deterministic feature extraction from database models for matching evaluation."""

from datetime import date, datetime, timezone
import re
from typing import Dict, List, Optional, Set

from app.matching.constants import SKILL_ALIASES, TITLE_ALIASES
from app.matching.models import CandidateMatchFeatures, JobMatchFeatures
from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.models.job_requirements import JobRequirements


def normalize_skill(skill_name: Optional[str]) -> str:
    """Deterministically normalize a skill name to canonical form."""
    if not skill_name:
        return ""
    cleaned = skill_name.strip().lower()
    # Direct alias lookup
    if cleaned in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned]
    # Remove leading/trailing non-alphanumeric except common symbols (c++, c#)
    cleaned_sub = re.sub(r"\s+", " ", cleaned)
    if cleaned_sub in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned_sub]
    return cleaned_sub


def normalize_title(title: Optional[str]) -> str:
    """Deterministically normalize a job title to canonical form."""
    if not title:
        return ""
    cleaned = title.strip().lower()
    # Replace separators with spaces
    cleaned = re.sub(r"[\-_/\\|,.]+", " ", cleaned)
    tokens = cleaned.split()
    normalized_tokens: List[str] = []
    for token in tokens:
        normalized_tokens.append(TITLE_ALIASES.get(token, token))
    normalized_str = " ".join(normalized_tokens)
    return normalized_str


def calculate_experience_years_from_history(experiences: list) -> float:
    """Calculate total non-overlapping or sequential experience in years from Experience records."""
    if not experiences:
        return 0.0
    total_days = 0
    today = date.today()
    for exp in experiences:
        start = exp.start_date
        if not start:
            continue
        end = exp.end_date if (exp.end_date and not exp.is_current) else today
        if end >= start:
            total_days += (end - start).days
    return round(total_days / 365.25, 1)


def extract_candidate_features(profile: CandidateProfile) -> CandidateMatchFeatures:
    """Extract structured CandidateMatchFeatures from CandidateProfile and related models."""
    skills_set: Set[str] = set()
    skill_experience: Dict[str, float] = {}

    if profile.skills:
        for cs in profile.skills:
            # Handle both loaded relationship and mock structures
            skill_name = cs.skill.name if hasattr(cs, "skill") and cs.skill else getattr(cs, "skill_name", "")
            norm = normalize_skill(skill_name)
            if norm:
                skills_set.add(norm)
                if cs.years_experience:
                    skill_experience[norm] = float(cs.years_experience)

    calculated_exp = calculate_experience_years_from_history(profile.experiences or [])
    total_exp = profile.years_of_experience
    if total_exp is None and calculated_exp > 0:
        total_exp = calculated_exp

    desired_titles: List[str] = []
    preferred_locations: List[str] = []
    workplace_types: List[str] = []
    employment_types: List[str] = []
    min_sal: Optional[int] = None
    max_sal: Optional[int] = None
    sal_curr: str = "USD"
    willing_relocate: bool = False
    remote_pref: Optional[str] = None

    if profile.preferences:
        pref = profile.preferences
        desired_titles = [normalize_title(t) for t in (pref.desired_titles or []) if t]
        preferred_locations = [loc.strip().lower() for loc in (pref.preferred_locations or []) if loc]
        workplace_types = [wt.upper() for wt in (pref.workplace_types or []) if wt]
        employment_types = [et.upper() for et in (pref.employment_types or []) if et]
        min_sal = pref.minimum_salary
        max_sal = pref.maximum_salary
        sal_curr = pref.salary_currency or "USD"
        willing_relocate = pref.willing_to_relocate or False
        remote_pref = pref.remote_preference

    degrees: List[str] = []
    if profile.educations:
        for edu in profile.educations:
            if edu.degree:
                degrees.append(edu.degree.strip().lower())

    return CandidateMatchFeatures(
        profile_id=profile.id,
        user_id=profile.user_id,
        skills=skills_set,
        skill_experience=skill_experience,
        total_experience_years=total_exp,
        calculated_experience_years=calculated_exp,
        current_title=normalize_title(profile.current_job_title) if profile.current_job_title else None,
        desired_titles=desired_titles,
        city=profile.city.strip().lower() if profile.city else None,
        state=profile.state.strip().lower() if profile.state else None,
        country=profile.country.strip().lower() if profile.country else None,
        preferred_locations=preferred_locations,
        willing_to_relocate=willing_relocate,
        remote_preference=remote_pref,
        workplace_types=workplace_types,
        employment_types=employment_types,
        minimum_salary=min_sal,
        maximum_salary=max_sal,
        salary_currency=sal_curr.upper() if sal_curr else "USD",
        highest_education_level=profile.highest_education_level.strip().lower() if profile.highest_education_level else None,
        degrees=degrees,
    )


def extract_job_features(job: Job, requirements: Optional[JobRequirements] = None) -> JobMatchFeatures:
    """Extract structured JobMatchFeatures from Job and optional JobRequirements."""
    # Check if requirements attached to job directly or passed explicitly
    req = requirements or getattr(job, "requirements", None)

    req_skills: Set[str] = set()
    pref_skills: Set[str] = set()
    min_exp: Optional[float] = None
    max_exp: Optional[float] = None
    min_sal: Optional[int] = None
    max_sal: Optional[int] = None
    sal_curr: Optional[str] = None
    req_edu: Optional[str] = None
    has_req = False

    if req:
        has_req = True
        if req.required_skills:
            req_skills = {normalize_skill(s) for s in req.required_skills if s}
        if req.preferred_skills:
            pref_skills = {normalize_skill(s) for s in req.preferred_skills if s}
        min_exp = req.minimum_experience_years
        max_exp = req.maximum_experience_years
        min_sal = req.minimum_salary
        max_sal = req.maximum_salary
        sal_curr = req.salary_currency.upper() if req.salary_currency else None
        req_edu = req.required_education_level.strip().lower() if req.required_education_level else None

    return JobMatchFeatures(
        job_id=job.id,
        title=job.title,
        location=job.location,
        workplace_type=job.workplace_type,
        employment_type=job.employment_type,
        has_requirements=has_req,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        minimum_experience_years=min_exp,
        maximum_experience_years=max_exp,
        minimum_salary=min_sal,
        maximum_salary=max_sal,
        salary_currency=sal_curr,
        required_education_level=req_edu,
    )
