"""Constants, versions, and status definitions for Phase 7 AI Intelligence."""

from enum import Enum
from typing import Dict

# Versioning identifiers
EXTRACTION_PROMPT_VERSION: str = "v1"
EXTRACTION_VERSION: str = "v1"

EXPLANATION_PROMPT_VERSION: str = "v1"
EXPLANATION_VERSION: str = "v1"

EMBEDDING_VERSION: str = "v1"
CANDIDATE_EMBEDDING_INPUT_VERSION: str = "v1"
JOB_EMBEDDING_INPUT_VERSION: str = "v1"

HYBRID_SCORING_VERSION: str = "v1"

# Default hybrid weights
DEFAULT_HYBRID_WEIGHTS: Dict[str, float] = {
    "deterministic": 0.70,
    "semantic": 0.30,
}

# Maximum characters from raw job description sent to LLM for extraction
MAX_DESCRIPTION_EXTRACTION_CHARS: int = 16000


class AIStatus(str, Enum):
    """Execution status of AI enrichment and semantic analysis."""

    AI_AVAILABLE = "AI_AVAILABLE"
    AI_PARTIAL = "AI_PARTIAL"
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    EXPLANATION_FAILED = "EXPLANATION_FAILED"
    DISABLED = "DISABLED"
