"""JobExtractor service for extracting structured criteria from raw job descriptions."""

import hashlib
import logging
import time
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.ai.config import EXTRACTION_PROMPT_VERSION, EXTRACTION_VERSION
from app.ai.extraction.prompts import build_job_extraction_prompts
from app.ai.extraction.schemas import AIJobRequirements
from app.ai.providers.base import LLMProvider
from app.ai.providers.openai_provider import AIProviderError
from app.models.job import Job
from app.repositories.ai_job_extraction import AIJobExtractionRepository
from app.repositories.job_requirements import JobRequirementsRepository

logger = logging.getLogger(__name__)


class JobExtractor:
    """Service responsible for extracting and caching structured job qualifications."""

    def __init__(
        self,
        db: Session,
        llm_provider: LLMProvider,
        model_name: str = "gpt-4o-mini",
    ) -> None:
        self.db = db
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.extraction_repo = AIJobExtractionRepository(db)
        self.job_req_repo = JobRequirementsRepository(db)

    @staticmethod
    def compute_hash(hash_content: str) -> str:
        """Compute SHA-256 hex digest for extraction cache checking."""
        return hashlib.sha256(hash_content.encode("utf-8")).hexdigest()

    def extract_requirements(
        self,
        job: Job,
        force_refresh: bool = False,
    ) -> Optional[AIJobRequirements]:
        """Extract structured criteria from job title and description.

        Returns AIJobRequirements if successful, or None on failure without raising.
        """
        system_prompt, user_prompt, hash_content = build_job_extraction_prompts(
            job_title=job.title,
            raw_description=job.description or "",
        )
        input_hash = self.compute_hash(hash_content)

        # 1. Check cache unless force refresh requested
        if not force_refresh:
            cached = self.extraction_repo.get_cached(
                job_id=job.id,
                input_hash=input_hash,
                model=self.model_name,
                prompt_version=EXTRACTION_PROMPT_VERSION,
            )
            if cached and cached.is_success and cached.structured_requirements:
                logger.info(
                    "ai.operation=job_extraction ai.cache=hit job_id=%s model=%s",
                    job.id,
                    self.model_name,
                )
                return AIJobRequirements.model_validate(cached.structured_requirements)

        # 2. Invoke LLM with performance timing
        start_time = time.perf_counter()
        logger.info(
            "ai.operation=job_extraction ai.cache=miss job_id=%s model=%s input_hash=%s",
            job.id,
            self.model_name,
            input_hash[:10],
        )

        try:
            extracted: AIJobRequirements = self.llm_provider.generate_structured_sync(
                schema=AIJobRequirements,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model_name,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # 3. Persist extraction record
            self.extraction_repo.save_extraction(
                job_id=job.id,
                input_hash=input_hash,
                model=self.model_name,
                prompt_version=EXTRACTION_PROMPT_VERSION,
                extraction_version=EXTRACTION_VERSION,
                structured_requirements=extracted.model_dump(),
                is_success=True,
                duration_ms=round(duration_ms, 2),
            )

            # 4. Sync into JobRequirements for deterministic engine integration
            self.job_req_repo.upsert(
                job_id=job.id,
                required_skills=extracted.required_skills,
                preferred_skills=extracted.preferred_skills,
                minimum_experience_years=extracted.minimum_experience_years,
                maximum_experience_years=extracted.maximum_experience_years,
                minimum_salary=extracted.minimum_salary,
                maximum_salary=extracted.maximum_salary,
                salary_currency=extracted.salary_currency or "USD",
                required_education_level=extracted.required_education_level,
            )

            logger.info(
                "ai.operation=job_extraction ai.success=true job_id=%s duration_ms=%.1f",
                job.id,
                duration_ms,
            )
            return extracted

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                "ai.operation=job_extraction ai.success=false job_id=%s error=%s duration_ms=%.1f",
                job.id,
                e,
                duration_ms,
            )
            self.extraction_repo.save_extraction(
                job_id=job.id,
                input_hash=input_hash,
                model=self.model_name,
                prompt_version=EXTRACTION_PROMPT_VERSION,
                extraction_version=EXTRACTION_VERSION,
                structured_requirements={},
                is_success=False,
                error_message=str(e),
                duration_ms=round(duration_ms, 2),
            )
            return None
