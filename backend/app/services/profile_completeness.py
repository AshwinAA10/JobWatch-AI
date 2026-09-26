"""Service calculating deterministic, explainable candidate profile completeness."""

from typing import Dict, List, Tuple
from app.models.candidate_profile import CandidateProfile
from app.schemas.candidate_profile import ProfileCompletenessResponse


class ProfileCompletenessService:
    """Computes transparent, deterministic profile completeness scores without AI or ML."""

    WEIGHT_BASIC_IDENTITY = 15
    WEIGHT_HEADLINE = 10
    WEIGHT_BIO = 10
    WEIGHT_SKILLS = 20
    WEIGHT_EXPERIENCE = 20
    WEIGHT_EDUCATION = 10
    WEIGHT_PREFERENCES = 15

    @classmethod
    def calculate(
        cls, profile: CandidateProfile
    ) -> Tuple[int, List[str], Dict[str, bool]]:
        """Calculate the completeness percentage and missing sections for a profile.

        Args:
            profile: CandidateProfile entity with loaded relationships.

        Returns:
            Tuple of:
            - completion_percent: int (0 to 100)
            - missing_sections: List of section names that are incomplete
            - breakdown: Dict mapping section names to boolean completion status
        """
        breakdown: Dict[str, bool] = {}
        missing_sections: List[str] = []
        score = 0

        # 1. Basic Identity (first name, last name, and at least one location indicator)
        has_basic_identity = bool(
            profile.first_name
            and profile.first_name.strip()
            and profile.last_name
            and profile.last_name.strip()
            and (
                (profile.city and profile.city.strip())
                or (profile.state and profile.state.strip())
                or (profile.country and profile.country.strip())
            )
        )
        breakdown["basic_identity"] = has_basic_identity
        if has_basic_identity:
            score += cls.WEIGHT_BASIC_IDENTITY
        else:
            missing_sections.append("basic_identity")

        # 2. Professional Headline / Current Role
        has_headline = bool(
            (profile.headline and profile.headline.strip())
            or (profile.current_job_title and profile.current_job_title.strip())
        )
        breakdown["headline"] = has_headline
        if has_headline:
            score += cls.WEIGHT_HEADLINE
        else:
            missing_sections.append("headline")

        # 3. Professional Bio / Summary
        has_bio = bool(profile.bio and profile.bio.strip())
        breakdown["bio"] = has_bio
        if has_bio:
            score += cls.WEIGHT_BIO
        else:
            missing_sections.append("bio")

        # 4. Skills (At least 1 candidate skill attached)
        has_skills = bool(profile.skills and len(profile.skills) > 0)
        breakdown["skills"] = has_skills
        if has_skills:
            score += cls.WEIGHT_SKILLS
        else:
            missing_sections.append("skills")

        # 5. Work Experience (At least 1 experience record)
        has_experience = bool(profile.experiences and len(profile.experiences) > 0)
        breakdown["experience"] = has_experience
        if has_experience:
            score += cls.WEIGHT_EXPERIENCE
        else:
            missing_sections.append("experience")

        # 6. Education (At least 1 education record)
        has_education = bool(profile.educations and len(profile.educations) > 0)
        breakdown["education"] = has_education
        if has_education:
            score += cls.WEIGHT_EDUCATION
        else:
            missing_sections.append("education")

        # 7. Job Preferences (Structured preferences defined with at least one criteria)
        has_preferences = False
        if profile.preferences is not None:
            prefs = profile.preferences
            has_preferences = bool(
                (prefs.desired_titles and len(prefs.desired_titles) > 0)
                or (prefs.preferred_locations and len(prefs.preferred_locations) > 0)
                or (prefs.workplace_types and len(prefs.workplace_types) > 0)
                or (prefs.minimum_salary is not None)
            )
        breakdown["preferences"] = has_preferences
        if has_preferences:
            score += cls.WEIGHT_PREFERENCES
        else:
            missing_sections.append("preferences")

        # Cap score between 0 and 100
        score = min(100, max(0, score))
        return score, missing_sections, breakdown

    @classmethod
    def get_completeness_response(
        cls, profile: CandidateProfile
    ) -> ProfileCompletenessResponse:
        """Return schema response for profile completeness."""
        score, missing, breakdown = cls.calculate(profile)
        return ProfileCompletenessResponse(
            profile_completion_percent=score,
            missing_sections=missing,
            breakdown=breakdown,
        )
