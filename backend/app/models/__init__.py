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
]
