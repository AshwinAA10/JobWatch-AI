"""Semantic search and discovery engine over job embeddings and career similarities."""

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.ai.embeddings.service import EmbeddingService
from app.ai.providers.base import EmbeddingProvider
from app.models.job import Job
from app.repositories.job import JobRepository
from app.repositories.job_embedding import JobEmbeddingRepository


class SemanticSearchService:
    """Executes natural language semantic searches and discovers similar/adjacent job postings."""

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.embedding_provider = embedding_provider
        self.job_repo = JobRepository(db)
        self.embedding_repo = JobEmbeddingRepository(db)

    def search_jobs(
        self,
        query: str,
        limit: int = 20,
        min_similarity: float = 0.20,
        workplace_type: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search jobs using natural language query embedding compared against active job vectors."""
        if not query or not query.strip():
            return []

        # 1. Embed user query text
        query_vectors = self.embedding_provider.embed_sync([query.strip()])
        if not query_vectors or not query_vectors[0]:
            return []
        query_vector = query_vectors[0]

        # 2. Retrieve job embeddings and rank by cosine similarity
        all_embeddings = self.embedding_repo.list_all_active_embeddings(limit=500)
        scored_jobs: List[Tuple[Job, float]] = []

        for record in all_embeddings:
            if not record.embedding:
                continue

            similarity = self.embedding_service.calculate_cosine_similarity(
                query_vector,
                list(record.embedding),
            )
            if similarity < min_similarity:
                continue

            job = self.job_repo.get_by_id(record.job_id)
            if not job or not job.is_active:
                continue

            # Apply hard filters if requested
            if workplace_type and job.workplace_type != workplace_type:
                continue
            if location and location.lower() not in (job.location or "").lower():
                continue

            scored_jobs.append((job, similarity))

        # Sort descending by similarity
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored_jobs[:limit]

        return [
            {
                "job_id": job.id,
                "title": job.title,
                "company_name": job.company.name if job.company else None,
                "location": job.location,
                "workplace_type": job.workplace_type,
                "semantic_similarity": round(sim, 3),
                "relevance_score": round(sim * 100, 1),
            }
            for job, sim in top_matches
        ]

    def find_similar_jobs(
        self,
        job_id: UUID,
        limit: int = 5,
        min_similarity: float = 0.35,
    ) -> List[Dict[str, Any]]:
        """Find related career opportunities matching the target job vector representation."""
        source_job = self.job_repo.get_by_id(job_id)
        if not source_job:
            return []

        source_vector = self.embedding_service.get_or_create_job_embedding(source_job)
        if not source_vector:
            return []

        all_embeddings = self.embedding_repo.list_all_active_embeddings(limit=500)
        similar_list = []

        for record in all_embeddings:
            if record.job_id == job_id or not record.embedding:
                continue

            similarity = self.embedding_service.calculate_cosine_similarity(
                source_vector,
                list(record.embedding),
            )
            if similarity < min_similarity:
                continue

            other_job = self.job_repo.get_by_id(record.job_id)
            if not other_job or not other_job.is_active:
                continue

            # Determine reason label from similarity
            reason = "Similar technology stack & domain"
            if other_job.workplace_type == source_job.workplace_type:
                reason += f" ({other_job.workplace_type})"

            similar_list.append({
                "job_id": other_job.id,
                "title": other_job.title,
                "company_name": other_job.company.name if other_job.company else None,
                "location": other_job.location,
                "workplace_type": other_job.workplace_type,
                "similarity": round(similarity, 3),
                "match_reason": reason,
            })

        similar_list.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_list[:limit]
