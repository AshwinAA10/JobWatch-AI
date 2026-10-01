"""Database models layer for JobWatch AI (Phase 1)."""

from app.models.base import Base, GUID, TimestampMixin
from app.models.ai_explanation import AIExplanation
from app.models.ai_job_extraction import AIJobExtraction
from app.models.candidate_embedding import CandidateEmbedding
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_duplicate import (
    JobDuplicate,
    MatchType,
)
from app.models.job_embedding import JobEmbedding
from app.models.job_match import JobMatch
from app.models.job_requirements import JobRequirements
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

from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.notification_preference import NotificationPreference

__all__ = [
    "Base",
    "GUID",
    "TimestampMixin",
    "Company",
    "CareerSource",
    "Job",
    "JobRequirements",
    "JobMatch",
    "AIJobExtraction",
    "JobEmbedding",
    "CandidateEmbedding",
    "AIExplanation",
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
    "Notification",
    "NotificationDelivery",
    "NotificationPreference",
]
