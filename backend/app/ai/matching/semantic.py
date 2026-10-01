"""SemanticMatcher computing semantic similarity score between candidate and job vectors."""

from typing import Any, Dict, List, Optional
from app.ai.embeddings.service import EmbeddingService


class SemanticMatcher:
    """Calculates semantic relevance score from vector representations."""

    @staticmethod
    def compare_vectors(
        candidate_vector: Optional[List[float]],
        job_vector: Optional[List[float]],
    ) -> Optional[Dict[str, Any]]:
        """Calculate cosine similarity and scale to 0-100 score.

        Returns None if either vector is unavailable.
        """
        if not candidate_vector or not job_vector:
            return None

        similarity = EmbeddingService.calculate_cosine_similarity(
            candidate_vector,
            job_vector,
        )
        score = round(similarity * 100.0, 1)

        return {
            "similarity": round(similarity, 4),
            "score": score,
        }
