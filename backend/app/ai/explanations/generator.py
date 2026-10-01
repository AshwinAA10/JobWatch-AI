"""AIExplanationGenerator synthesizing narrative explanations from structured match results."""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.ai.config import EXPLANATION_PROMPT_VERSION, EXPLANATION_VERSION
from app.ai.explanations.prompts import (
    EXPLANATION_SYSTEM_PROMPT_V1,
    AIExplanationSchema,
    build_explanation_payload,
)
from app.ai.providers.base import LLMProvider
from app.repositories.ai_explanation import AIExplanationRepository

logger = logging.getLogger(__name__)


class AIExplanationGenerator:
    """Service generating narrative match explanations with deterministic fallback."""

    def __init__(
        self,
        db: Session,
        llm_provider: LLMProvider,
        model_name: str = "gpt-4o-mini",
    ) -> None:
        self.db = db
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.repo = AIExplanationRepository(db)

    @staticmethod
    def compute_input_hash(data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of structured match data for caching."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def generate_explanation(
        self,
        profile_id: UUID,
        job_id: UUID,
        job_title: str,
        deterministic_score: float,
        semantic_score: Optional[float],
        hybrid_score: float,
        matched_criteria: List[str],
        missing_criteria: List[str],
        mismatches: List[str],
        deterministic_reasons: List[str],
        ai_enabled: bool = True,
    ) -> AIExplanationSchema:
        """Generate narrative explanation with caching and deterministic fallback."""
        sem_score = semantic_score if semantic_score is not None else deterministic_score

        hash_payload = {
            "profile_id": str(profile_id),
            "job_id": str(job_id),
            "det": deterministic_score,
            "sem": sem_score,
            "hybrid": hybrid_score,
            "matched": sorted(matched_criteria),
            "missing": sorted(missing_criteria),
            "mismatches": sorted(mismatches),
            "prompt_version": EXPLANATION_PROMPT_VERSION,
        }
        input_hash = self.compute_input_hash(hash_payload)

        # 1. Check cache
        cached = self.repo.get_cached(
            profile_id=profile_id,
            job_id=job_id,
            input_hash=input_hash,
            model=self.model_name,
            prompt_version=EXPLANATION_PROMPT_VERSION,
        )
        if cached:
            logger.info("ai.operation=explanation ai.cache=hit job_id=%s", job_id)
            return AIExplanationSchema(
                summary=cached.summary,
                strengths=cached.strengths,
                gaps=cached.gaps,
                recommendation=cached.recommendation,
            )

        # 2. If AI is disabled, generate deterministic fallback
        if not ai_enabled:
            return self._build_deterministic_fallback(
                job_title=job_title,
                deterministic_score=deterministic_score,
                hybrid_score=hybrid_score,
                matched_criteria=matched_criteria,
                missing_criteria=missing_criteria,
                reasons=deterministic_reasons,
            )

        # 3. Call LLM for narrative generation
        user_prompt = build_explanation_payload(
            job_title=job_title,
            deterministic_score=deterministic_score,
            semantic_score=sem_score,
            hybrid_score=hybrid_score,
            matched_criteria=matched_criteria,
            missing_criteria=missing_criteria,
            mismatches=mismatches,
            deterministic_reasons=deterministic_reasons,
        )

        try:
            explanation: AIExplanationSchema = self.llm_provider.generate_structured_sync(
                schema=AIExplanationSchema,
                system_prompt=EXPLANATION_SYSTEM_PROMPT_V1,
                user_prompt=user_prompt,
                model=self.model_name,
            )

            # Persist successful explanation
            self.repo.save_explanation(
                profile_id=profile_id,
                job_id=job_id,
                input_hash=input_hash,
                model=self.model_name,
                prompt_version=EXPLANATION_PROMPT_VERSION,
                explanation_version=EXPLANATION_VERSION,
                summary=explanation.summary,
                strengths=explanation.strengths,
                gaps=explanation.gaps,
                recommendation=explanation.recommendation,
            )
            return explanation

        except Exception as e:
            logger.error("Failed to generate AI explanation for job %s: %s", job_id, e)
            # Safe deterministic fallback
            return self._build_deterministic_fallback(
                job_title=job_title,
                deterministic_score=deterministic_score,
                hybrid_score=hybrid_score,
                matched_criteria=matched_criteria,
                missing_criteria=missing_criteria,
                reasons=deterministic_reasons,
            )

    @staticmethod
    def _build_deterministic_fallback(
        job_title: str,
        deterministic_score: float,
        hybrid_score: float,
        matched_criteria: List[str],
        missing_criteria: List[str],
        reasons: List[str],
    ) -> AIExplanationSchema:
        """Produce clean rule-based fallback explanation when LLM is unavailable."""
        summary = (
            f"Candidate profile scored {deterministic_score:.0f}/100 on deterministic rules "
            f"and achieved an overall hybrid match score of {hybrid_score:.0f}/100 for {job_title}."
        )
        strengths = matched_criteria[:4] if matched_criteria else ["Profile matches basic role prerequisites."]
        gaps = missing_criteria[:3] if missing_criteria else ["No critical requirement gaps detected."]
        recommendation = (
            "Review role requirements and emphasize your verified matching skills in your application."
        )
        return AIExplanationSchema(
            summary=summary,
            strengths=strengths,
            gaps=gaps,
            recommendation=recommendation,
        )
