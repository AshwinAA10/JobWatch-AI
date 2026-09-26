"""Domain enumerations for user profiles, skills, and preferences."""

from enum import Enum


class ProficiencyLevel(str, Enum):
    """Proficiency level for candidate skills."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class WorkplaceType(str, Enum):
    """Workplace location flexibility."""

    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"


class EmploymentType(str, Enum):
    """Employment arrangement classification."""

    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    TEMPORARY = "TEMPORARY"


class ProfileVisibility(str, Enum):
    """Candidate profile privacy visibility."""

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
