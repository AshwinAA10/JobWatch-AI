"""Deduplication and Job Identity domain package (Phase 4)."""

from app.deduplication.exceptions import (
    CanonicalCycleError,
    DeduplicationError,
    JobNotFoundError,
    SelfDuplicateError,
)
from app.deduplication.normalizers import (
    clean_text,
    extract_seniority,
    normalize_location,
    normalize_title,
    normalize_url,
)
from app.deduplication.schemas import (
    DedupRunResponse,
    DedupStatusResponse,
    JobDuplicateRead,
    MatchResult,
)
from app.deduplication.scoring import evaluate_job_pair
from app.deduplication.service import DeduplicationService
from app.models.job_duplicate import JobDuplicate, MatchType
from app.repositories.job_duplicate import JobDuplicateRepository

__all__ = [
    "DeduplicationService",
    "JobDuplicateRepository",
    "JobDuplicate",
    "MatchType",
    "MatchResult",
    "JobDuplicateRead",
    "DedupStatusResponse",
    "DedupRunResponse",
    "evaluate_job_pair",
    "normalize_title",
    "normalize_location",
    "normalize_url",
    "clean_text",
    "extract_seniority",
    "DeduplicationError",
    "CanonicalCycleError",
    "SelfDuplicateError",
    "JobNotFoundError",
]
