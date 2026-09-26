"""Database models layer for JobWatch AI (Phase 1)."""

from app.models.base import Base, GUID, TimestampMixin
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_duplicate import (
    JobDuplicate,
    MatchType,
)
from app.models.monitoring_run import (
    MonitoringRun,
    MonitoringRunStatus,
    MonitoringTriggerType,
)

from app.models.candidate_preferences import CandidatePreferences
from app.models.candidate_profile import CandidateProfile
from app.models.candidate_skill import CandidateSkill
from app.models.education import Education
from app.models.enums import (
    EmploymentType,
    ProficiencyLevel,
    ProfileVisibility,
    WorkplaceType,
)
from app.models.experience import Experience
from app.models.resume import Resume
from app.models.skill import Skill
from app.models.user import User

__all__ = [
    "Base",
    "GUID",
    "TimestampMixin",
    "Company",
    "CareerSource",
    "Job",
    "JobDuplicate",
    "MatchType",
    "MonitoringRun",
    "MonitoringRunStatus",
    "MonitoringTriggerType",
    "User",
    "CandidateProfile",
    "Skill",
    "CandidateSkill",
    "Experience",
    "Education",
    "CandidatePreferences",
    "Resume",
    "ProficiencyLevel",
    "WorkplaceType",
    "EmploymentType",
    "ProfileVisibility",
]
