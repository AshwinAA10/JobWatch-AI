"""Repository for AIJobExtraction entity persistence operations."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_job_extraction import AIJobExtraction


class AIJobExtractionRepository:
    """Data access repository for AIJobExtraction records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_job_id(self, job_id: UUID) -> Optional[AIJobExtraction]:
        """Fetch latest successful extraction for a job."""
        stmt = (
            select(AIJobExtraction)
            .where(AIJobExtraction.job_id == job_id, AIJobExtraction.is_success.is_(True))
            .order_by(AIJobExtraction.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_latest_for_job(self, job_id: UUID) -> Optional[AIJobExtraction]:
        """Fetch the latest extraction for a job regardless of success status."""
        stmt = (
            select(AIJobExtraction)
            .where(AIJobExtraction.job_id == job_id)
            .order_by(AIJobExtraction.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_cached(
        self,
        job_id: UUID,
        input_hash: str,
        model: str,
        prompt_version: str,
    ) -> Optional[AIJobExtraction]:
        """Fetch cached extraction matching exact input hash, model, and prompt version."""
        stmt = select(AIJobExtraction).where(
            AIJobExtraction.job_id == job_id,
            AIJobExtraction.input_hash == input_hash,
            AIJobExtraction.model == model,
            AIJobExtraction.prompt_version == prompt_version,
            AIJobExtraction.is_success.is_(True),
        )
        return self.db.scalars(stmt).first()

    def save_extraction(
        self,
        job_id: UUID,
        input_hash: str,
        model: str,
        prompt_version: str,
        extraction_version: str,
        structured_requirements: Dict[str, Any],
        is_success: bool = True,
        error_message: Optional[str] = None,
        tokens_used: Optional[int] = None,
        duration_ms: Optional[float] = None,
    ) -> AIJobExtraction:
        """Create or update an AIJobExtraction record."""
        existing = self.db.scalars(
            select(AIJobExtraction).where(
                AIJobExtraction.job_id == job_id,
                AIJobExtraction.input_hash == input_hash,
                AIJobExtraction.model == model,
                AIJobExtraction.prompt_version == prompt_version,
            )
        ).first()

        if existing:
            existing.extraction_version = extraction_version
            existing.structured_requirements = structured_requirements
            existing.is_success = is_success
            existing.error_message = error_message
            existing.tokens_used = tokens_used
            existing.duration_ms = duration_ms
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = AIJobExtraction(
            job_id=job_id,
            input_hash=input_hash,
            model=model,
            prompt_version=prompt_version,
            extraction_version=extraction_version,
            structured_requirements=structured_requirements,
            is_success=is_success,
            error_message=error_message,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
