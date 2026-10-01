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


class ApplicationStatus(str, Enum):
    """Lifecycle statuses for candidate job applications."""

    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ACCEPTED = "ACCEPTED"


class InterviewType(str, Enum):
    """Category classification for job interviews."""

    PHONE = "PHONE"
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    BEHAVIORAL = "BEHAVIORAL"
    MANAGERIAL = "MANAGERIAL"
    FINAL = "FINAL"
    OTHER = "OTHER"


class InterviewStatus(str, Enum):
    """Execution status for scheduled interviews."""

    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"

