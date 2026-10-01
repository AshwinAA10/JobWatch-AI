"""AIIntelligenceService orchestrating extraction, embeddings, semantic and hybrid matching."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.ai.config import AIStatus
from app.ai.embeddings.service import EmbeddingService
from app.ai.explanations.generator import AIExplanationGenerator
from app.ai.extraction.job_extractor import JobExtractor
from app.ai.extraction.schemas import AIJobRequirements
from app.ai.matching.hybrid import HybridMatcher, HybridMatchOutcome
from app.ai.matching.semantic import SemanticMatcher
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import get_settings
from app.models.ai_job_extraction import AIJobExtraction
from app.models.job import Job
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.job import JobRepository
from app.schemas.ai import AIExplanationResponse, EnhancedMatchResponse
from app.services.exceptions import JobNotFoundError, ProfileNotFoundError
from app.services.matching import MatchingService

logger = logging.getLogger(__name__)


class AIIntelligenceService:
    """Master coordinator for Phase 7 AI capabilities."""

    def __init__(
        self,
        db: Session,
        llm_provider: Optional[LLMProvider] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.db = db
        settings = get_settings()

        # Initialize provider with fallback to FakeProvider when no API key configured
        if llm_provider is not None:
            self.llm_provider = llm_provider
        elif settings.OPENAI_API_KEY:
            self.llm_provider = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                embedding_model=settings.OPENAI_EMBEDDING_MODEL,
                embedding_dimensions=settings.OPENAI_EMBEDDING_DIMENSION,
                timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES,
            )
        else:
            self.llm_provider = FakeProvider(dimensions=settings.OPENAI_EMBEDDING_DIMENSION)

        if embedding_provider is not None:
            self.embedding_provider = embedding_provider
        elif isinstance(self.llm_provider, EmbeddingProvider):
            self.embedding_provider = self.llm_provider
        elif settings.OPENAI_API_KEY:
            self.embedding_provider = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                embedding_model=settings.OPENAI_EMBEDDING_MODEL,
                embedding_dimensions=settings.OPENAI_EMBEDDING_DIMENSION,
                timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES,
            )
        else:
            self.embedding_provider = FakeProvider(dimensions=settings.OPENAI_EMBEDDING_DIMENSION)

        # Domain subsystems
        self.extractor = JobExtractor(db, self.llm_provider, model_name=settings.OPENAI_MODEL)
        self.embeddings = EmbeddingService(
            db,
            self.embedding_provider,
            model_name=settings.OPENAI_EMBEDDING_MODEL,
        )
        self.semantic_matcher = SemanticMatcher()
        self.hybrid_matcher = HybridMatcher(
            deterministic_weight=settings.HYBRID_DETERMINISTIC_WEIGHT,
            semantic_weight=settings.HYBRID_SEMANTIC_WEIGHT,
        )
        self.explanation_generator = AIExplanationGenerator(
            db,
            self.llm_provider,
            model_name=settings.OPENAI_MODEL,
        )
        self.matching_service = MatchingService(db)
        self.job_repo = JobRepository(db)
        self.profile_repo = CandidateProfileRepository(db)

    def extract_job_requirements(
        self,
        job_id: UUID,
        force_refresh: bool = False,
    ) -> Optional[AIJobRequirements]:
        """Run or fetch structured requirements extraction for a job opening."""
        settings = get_settings()
        if not settings.AI_EXTRACTION_ENABLED:
            logger.info("AI extraction disabled by feature flag.")
            return None

        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        return self.extractor.extract_requirements(job, force_refresh=force_refresh)

    def get_cached_job_extraction(self, job_id: UUID) -> Optional[AIJobExtraction]:
        """Fetch cached extraction record from DB if existing."""
        return self.extractor.extraction_repo.get_by_job_id(job_id)

    def evaluate_enhanced_match(
        self,
        user_id: UUID,
        job_id: UUID,
        force_refresh: bool = False,
    ) -> EnhancedMatchResponse:
        """Execute AI-enhanced hybrid matching between authenticated user and job."""
        settings = get_settings()

        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(user_id=user_id)

        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id=job_id)

        # 1. Authoritative Phase 6 Deterministic Baseline
        deterministic_resp = self.matching_service.match_candidate_to_job(
            user_id=user_id,
            job_id=job_id,
            persist=True,
        )

        # Convert schema response to MatchResult-compatible structure for hybrid matcher
        from app.matching.models import MatchResult
        det_result = MatchResult(
            job_id=job_id,
            profile_id=profile.id,
            score=deterministic_resp.score,
            confidence=deterministic_resp.confidence or "MEDIUM",
            scoring_version=deterministic_resp.scoring_version,
            breakdown=deterministic_resp.breakdown,
            matched_criteria=deterministic_resp.matched_criteria,
            missing_criteria=deterministic_resp.missing_criteria,
            mismatches=deterministic_resp.mismatches,
            reasons=deterministic_resp.reasons,
        )

        # 2. Semantic vector analysis (if enabled)
        semantic_data: Optional[Dict[str, Any]] = None
        if settings.AI_EMBEDDING_ENABLED:
            try:
                cand_vec = self.embeddings.get_or_create_candidate_embedding(
                    profile,
                    force_refresh=force_refresh,
                )
                job_vec = self.embeddings.get_or_create_job_embedding(
                    job,
                    force_refresh=force_refresh,
                )
                semantic_data = self.semantic_matcher.compare_vectors(cand_vec, job_vec)
            except Exception as e:
                logger.error("Semantic embedding comparison failed for job %s: %s", job_id, e)
                semantic_data = None

        # 3. Hybrid synthesis with safety guardrails
        hybrid_outcome: HybridMatchOutcome = self.hybrid_matcher.combine(
            deterministic_result=det_result,
            semantic_data=semantic_data,
            ai_enabled=settings.AI_HYBRID_MATCHING_ENABLED,
        )

        # 4. Narrative AI explanation (with deterministic fallback)
        ai_expl = self.explanation_generator.generate_explanation(
            profile_id=profile.id,
            job_id=job.id,
            job_title=job.title,
            deterministic_score=deterministic_resp.score,
            semantic_score=hybrid_outcome.semantic_score,
            hybrid_score=hybrid_outcome.hybrid_score,
            matched_criteria=deterministic_resp.matched_criteria,
            missing_criteria=deterministic_resp.missing_criteria,
            mismatches=deterministic_resp.mismatches,
            deterministic_reasons=deterministic_resp.reasons,
            ai_enabled=settings.AI_EXPLANATIONS_ENABLED,
        )

        explanation_response = AIExplanationResponse(
            summary=ai_expl.summary,
            strengths=ai_expl.strengths,
            gaps=ai_expl.gaps,
            recommendation=ai_expl.recommendation,
        )

        return EnhancedMatchResponse(
            job_id=job.id,
            profile_id=profile.id,
            deterministic_score=deterministic_resp.score,
            semantic_score=hybrid_outcome.semantic_score,
            hybrid_score=hybrid_outcome.hybrid_score,
            scoring_version=deterministic_resp.scoring_version,
            ai_status=hybrid_outcome.ai_status,
            embedding_model=settings.OPENAI_EMBEDDING_MODEL if settings.AI_EMBEDDING_ENABLED else None,
            guardrail_applied=hybrid_outcome.guardrail_applied,
            breakdown=deterministic_resp.breakdown,
            semantic_details=semantic_data,
            matched_criteria=deterministic_resp.matched_criteria,
            missing_criteria=deterministic_resp.missing_criteria,
            mismatches=deterministic_resp.mismatches,
            reasons=deterministic_resp.reasons,
            explanation=explanation_response,
            calculated_at=datetime.now(timezone.utc),
        )
