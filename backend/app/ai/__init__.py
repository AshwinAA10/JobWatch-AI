"""JobWatch AI - Phase 7: AI Intelligence & Semantic Matching Layer."""

from app.ai.config import (
    AIStatus,
    DEFAULT_HYBRID_WEIGHTS,
    EMBEDDING_VERSION,
    EXPLANATION_PROMPT_VERSION,
    EXTRACTION_PROMPT_VERSION,
    HYBRID_SCORING_VERSION,
)
from app.ai.embeddings.service import EmbeddingService
from app.ai.explanations.generator import AIExplanationGenerator
from app.ai.extraction.job_extractor import JobExtractor
from app.ai.extraction.schemas import AIJobRequirements
from app.ai.matching.hybrid import HybridMatcher, HybridMatchOutcome
from app.ai.matching.semantic import SemanticMatcher
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.service import AIIntelligenceService

__all__ = [
    "AIIntelligenceService",
    "LLMProvider",
    "EmbeddingProvider",
    "OpenAIProvider",
    "FakeProvider",
    "JobExtractor",
    "AIJobRequirements",
    "EmbeddingService",
    "SemanticMatcher",
    "HybridMatcher",
    "HybridMatchOutcome",
    "AIExplanationGenerator",
    "AIStatus",
    "EXTRACTION_PROMPT_VERSION",
    "EXPLANATION_PROMPT_VERSION",
    "EMBEDDING_VERSION",
    "HYBRID_SCORING_VERSION",
    "DEFAULT_HYBRID_WEIGHTS",
]
