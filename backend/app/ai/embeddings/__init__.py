"""AI embeddings package."""

from app.ai.embeddings.models import (
    build_candidate_embedding_text,
    build_job_embedding_text,
)
from app.ai.embeddings.service import EmbeddingService

__all__ = [
    "EmbeddingService",
    "build_candidate_embedding_text",
    "build_job_embedding_text",
]
