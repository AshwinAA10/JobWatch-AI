"""Deterministic mock provider for unit and integration testing without external API calls."""

import hashlib
import math
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.providers.openai_provider import AIProviderError, AIRateLimitError, AITimeoutError

T = TypeVar("T", bound=BaseModel)


class FakeProvider(LLMProvider, EmbeddingProvider):
    """Deterministic test provider simulating LLM completions and embeddings."""

    def __init__(
        self,
        dimensions: int = 1536,
        structured_override: Optional[Any] = None,
        text_override: Optional[str] = None,
        should_fail: bool = False,
        failure_type: str = "generic",
    ) -> None:
        self._dimensions = dimensions
        self.structured_override = structured_override
        self.text_override = text_override
        self.should_fail = should_fail
        self.failure_type = failure_type

        # Call tracking counters for caching and cost verification
        self.call_count_structured: int = 0
        self.call_count_text: int = 0
        self.call_count_embed: int = 0

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _check_simulated_failure(self) -> None:
        """Raise simulated failure if configured."""
        if self.should_fail:
            if self.failure_type == "rate_limit":
                raise AIRateLimitError("Simulated OpenAI rate limit")
            elif self.failure_type == "timeout":
                raise AITimeoutError("Simulated OpenAI timeout")
            raise AIProviderError("Simulated OpenAI generic error")

    def generate_structured_sync(
        self,
        schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> T:
        """Return structured response conforming to schema."""
        self.call_count_structured += 1
        self._check_simulated_failure()

        if self.structured_override is not None:
            if isinstance(self.structured_override, schema):
                return self.structured_override
            elif isinstance(self.structured_override, dict):
                return schema.model_validate(self.structured_override)

        # Build default realistic extraction based on schema fields
        field_defaults: Dict[str, Any] = {}
        for name, field_info in schema.model_fields.items():
            ann = str(field_info.annotation)
            if "List[str]" in ann or "list[str]" in ann:
                field_defaults[name] = ["Python", "FastAPI"] if "skill" in name else []
            elif "float" in ann:
                field_defaults[name] = 3.0 if "min" in name else None
            elif "int" in ann:
                field_defaults[name] = 100000 if "min" in name else 150000
            elif "str" in ann:
                field_defaults[name] = "REMOTE" if "workplace" in name else "USD" if "currency" in name else None
            else:
                field_defaults[name] = None

        return schema.model_validate(field_defaults)

    def generate_text_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> str:
        """Return simulated narrative explanation."""
        self.call_count_text += 1
        self._check_simulated_failure()

        if self.text_override is not None:
            return self.text_override

        return "Candidate strongly aligns with technical requirements. Possesses key skills in Python and FastAPI."

    def embed_sync(
        self,
        texts: List[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate deterministic unit-norm vector embeddings derived from text SHA-256."""
        self.call_count_embed += 1
        self._check_simulated_failure()

        vectors: List[List[float]] = []
        for text in texts:
            # Deterministic pseudo-random seed from hash
            h = hashlib.sha256(text.encode("utf-8")).digest()
            raw_floats: List[float] = []
            for i in range(self._dimensions):
                byte_val = h[i % len(h)]
                # Map to [-1.0, 1.0] with variation based on position
                val = (byte_val / 128.0 - 1.0) * math.cos(i + 1)
                raw_floats.append(val)

            # L2 normalize
            norm = math.sqrt(sum(x * x for x in raw_floats))
            if norm > 0:
                normalized = [x / norm for x in raw_floats]
            else:
                normalized = [0.0] * self._dimensions
            vectors.append(normalized)

        return vectors
