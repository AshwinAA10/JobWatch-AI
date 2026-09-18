"""Business logic and service orchestration layer for JobWatch AI (Phase 2)."""

from app.services.ingestion import IngestionResult, JobIngestionService

__all__ = [
    "JobIngestionService",
    "IngestionResult",
]
