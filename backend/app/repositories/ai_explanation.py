"""Repository for AIExplanation entity persistence operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_explanation import AIExplanation


class AIExplanationRepository:
    """Data access repository for AIExplanation records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_profile_and_job(
        self,
        profile_id: UUID,
        job_id: UUID,
    ) -> Optional[AIExplanation]:
        """Fetch the most recent AIExplanation record for a profile and job pair."""
        stmt = (
            select(AIExplanation)
            .where(
                AIExplanation.profile_id == profile_id,
                AIExplanation.job_id == job_id,
            )
            .order_by(AIExplanation.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_cached(
        self,
        profile_id: UUID,
        job_id: UUID,
        input_hash: str,
        model: str,
        prompt_version: str,
    ) -> Optional[AIExplanation]:
        """Fetch cached narrative explanation matching exact input hash, model, and version."""
        stmt = select(AIExplanation).where(
            AIExplanation.profile_id == profile_id,
            AIExplanation.job_id == job_id,
            AIExplanation.input_hash == input_hash,
            AIExplanation.model == model,
            AIExplanation.prompt_version == prompt_version,
        )
        return self.db.scalars(stmt).first()

    def save_explanation(
        self,
        profile_id: UUID,
        job_id: UUID,
        input_hash: str,
        model: str,
        prompt_version: str,
        explanation_version: str,
        summary: str,
        strengths: List[str],
        gaps: List[str],
        recommendation: str,
    ) -> AIExplanation:
        """Create or update an AIExplanation record."""
        existing = self.db.scalars(
            select(AIExplanation).where(
                AIExplanation.profile_id == profile_id,
                AIExplanation.job_id == job_id,
                AIExplanation.input_hash == input_hash,
                AIExplanation.model == model,
                AIExplanation.prompt_version == prompt_version,
            )
        ).first()

        if existing:
            existing.summary = summary
            existing.strengths = strengths
            existing.gaps = gaps
            existing.recommendation = recommendation
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = AIExplanation(
            profile_id=profile_id,
            job_id=job_id,
            input_hash=input_hash,
            model=model,
            prompt_version=prompt_version,
            explanation_version=explanation_version,
            summary=summary,
            strengths=strengths,
            gaps=gaps,
            recommendation=recommendation,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
