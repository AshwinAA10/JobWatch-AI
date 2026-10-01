"""Text representation builders for generating candidate and job embeddings."""

from typing import List, Optional
from app.ai.config import CANDIDATE_EMBEDDING_INPUT_VERSION, JOB_EMBEDDING_INPUT_VERSION
from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.models.job_requirements import JobRequirements


def build_candidate_embedding_text(profile: CandidateProfile) -> str:
    """Build a deterministic, PII-minimized text representation of a candidate profile."""
    parts: List[str] = [f"version:{CANDIDATE_EMBEDDING_INPUT_VERSION}"]

    # 1. Professional Title & Headline
    title = profile.current_job_title or profile.headline or ""
    if title:
        parts.append(f"Title: {title.strip()}")

    # 2. Desired Titles
    if profile.preferences and profile.preferences.desired_titles:
        desired = ", ".join(sorted(profile.preferences.desired_titles))
        parts.append(f"Target Roles: {desired}")

    # 3. Skills (alphabetically sorted for strict determinism)
    if profile.skills:
        skill_names = sorted(
            [cs.skill.name for cs in profile.skills if cs.skill and cs.skill.name]
        )
        if skill_names:
            parts.append(f"Skills: {', '.join(skill_names)}")

    # 4. Total Experience
    if profile.years_of_experience is not None:
        parts.append(f"Experience: {profile.years_of_experience:.1f} years")

    # 5. Work preferences
    if profile.preferences:
        pref = profile.preferences
        if pref.workplace_types:
            parts.append(f"Workplace: {', '.join(sorted(pref.workplace_types))}")
        if pref.employment_types:
            parts.append(f"Employment: {', '.join(sorted(pref.employment_types))}")
        if pref.preferred_locations:
            parts.append(f"Locations: {', '.join(sorted(pref.preferred_locations))}")
        if pref.willing_to_relocate:
            parts.append("Willing to relocate: yes")

    # 6. Education
    if profile.highest_education_level:
        parts.append(f"Education: {profile.highest_education_level}")

    return "\n".join(parts)


def build_job_embedding_text(job: Job, requirements: Optional[JobRequirements] = None) -> str:
    """Build a deterministic text representation of a job opening and its requirements."""
    parts: List[str] = [f"version:{JOB_EMBEDDING_INPUT_VERSION}"]

    # 1. Title
    parts.append(f"Role: {job.title.strip()}")

    # 2. Workplace & Employment
    if job.workplace_type:
        parts.append(f"Workplace: {job.workplace_type}")
    if job.employment_type:
        parts.append(f"Employment: {job.employment_type}")
    if job.location:
        parts.append(f"Location: {job.location}")

    # 3. Structured requirements if available
    req = requirements or getattr(job, "requirements", None)
    if req:
        if req.required_skills:
            parts.append(f"Required Skills: {', '.join(sorted(req.required_skills))}")
        if req.preferred_skills:
            parts.append(f"Preferred Skills: {', '.join(sorted(req.preferred_skills))}")
        if req.minimum_experience_years is not None:
            parts.append(f"Minimum Experience: {req.minimum_experience_years:.1f} years")
        if req.required_education_level:
            parts.append(f"Required Education: {req.required_education_level}")

    # 4. Contextual summary from description (first 2,000 chars)
    if job.description:
        desc_clean = job.description.strip()
        parts.append(f"Description:\n{desc_clean[:2000]}")

    return "\n".join(parts)
