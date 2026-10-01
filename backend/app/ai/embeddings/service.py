"""EmbeddingService managing vector generation, content hashing, and caching."""

import hashlib
import logging
import math
from typing import List, Optional
from sqlalchemy.orm import Session

from app.ai.config import EMBEDDING_VERSION
from app.ai.embeddings.models import (
    build_candidate_embedding_text,
    build_job_embedding_text,
)
from app.ai.providers.base import EmbeddingProvider
from app.models.candidate_profile import CandidateProfile
from app.models.job import Job
from app.models.job_requirements import JobRequirements
from app.repositories.candidate_embedding import CandidateEmbeddingRepository
from app.repositories.job_embedding import JobEmbeddingRepository

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service responsible for generating, caching, and comparing vector embeddings."""

    def __init__(
        self,
        db: Session,
        embedding_provider: EmbeddingProvider,
        model_name: str = "text-embedding-3-small",
    ) -> None:
        self.db = db
        self.provider = embedding_provider
        self.model_name = model_name
        self.job_embedding_repo = JobEmbeddingRepository(db)
        self.candidate_embedding_repo = CandidateEmbeddingRepository(db)

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA-256 hash of text representation for cache invalidation."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two float vectors clamped to [0.0, 1.0]."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = 0.0
        norm_a_sq = 0.0
        norm_b_sq = 0.0

        for a, b in zip(vec_a, vec_b):
            dot += a * b
            norm_a_sq += a * a
            norm_b_sq += b * b

        if norm_a_sq <= 0.0 or norm_b_sq <= 0.0:
            return 0.0

        similarity = dot / (math.sqrt(norm_a_sq) * math.sqrt(norm_b_sq))
        # Clamp against floating point boundary conditions
        return max(0.0, min(1.0, float(similarity)))

    def get_or_create_job_embedding(
        self,
        job: Job,
        requirements: Optional[JobRequirements] = None,
        force_refresh: bool = False,
    ) -> Optional[List[float]]:
        """Fetch or generate embedding vector for a job."""
        text = build_job_embedding_text(job, requirements)
        content_hash = self.compute_hash(text)

        if not force_refresh:
            cached = self.job_embedding_repo.get_cached(
                job_id=job.id,
                content_hash=content_hash,
                model=self.model_name,
                embedding_version=EMBEDDING_VERSION,
            )
            if cached and cached.embedding:
                logger.info("ai.operation=job_embedding ai.cache=hit job_id=%s", job.id)
                # Convert to native list if needed
                return list(cached.embedding)

        logger.info("ai.operation=job_embedding ai.cache=miss job_id=%s", job.id)
        try:
            vectors = self.provider.embed_sync([text], model=self.model_name)
            if not vectors or not vectors[0]:
                logger.warning("Empty vector returned for job %s", job.id)
                return None

            vector = vectors[0]
            self.job_embedding_repo.save_embedding(
                job_id=job.id,
                content_hash=content_hash,
                model=self.model_name,
                dimensions=self.provider.dimensions,
                embedding_version=EMBEDDING_VERSION,
                embedding=vector,
            )
            return vector
        except Exception as e:
            logger.error("Failed to generate job embedding for %s: %s", job.id, e)
            return None

    def get_or_create_candidate_embedding(
        self,
        profile: CandidateProfile,
        force_refresh: bool = False,
    ) -> Optional[List[float]]:
        """Fetch or generate embedding vector for a candidate profile."""
        text = build_candidate_embedding_text(profile)
        content_hash = self.compute_hash(text)

        if not force_refresh:
            cached = self.candidate_embedding_repo.get_cached(
                profile_id=profile.id,
                content_hash=content_hash,
                model=self.model_name,
                embedding_version=EMBEDDING_VERSION,
            )
            if cached and cached.embedding:
                logger.info("ai.operation=candidate_embedding ai.cache=hit profile_id=%s", profile.id)
                return list(cached.embedding)

        logger.info("ai.operation=candidate_embedding ai.cache=miss profile_id=%s", profile.id)
        try:
            vectors = self.provider.embed_sync([text], model=self.model_name)
            if not vectors or not vectors[0]:
                logger.warning("Empty vector returned for profile %s", profile.id)
                return None

            vector = vectors[0]
            self.candidate_embedding_repo.save_embedding(
                profile_id=profile.id,
                content_hash=content_hash,
                model=self.model_name,
                dimensions=self.provider.dimensions,
                embedding_version=EMBEDDING_VERSION,
                embedding=vector,
            )
            return vector
        except Exception as e:
            logger.error("Failed to generate candidate embedding for %s: %s", profile.id, e)
            return None
