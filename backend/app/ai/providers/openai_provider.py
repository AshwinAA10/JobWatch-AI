"""OpenAI provider implementation for structured outputs and text embeddings."""

import logging
import time
from typing import Any, List, Optional, Type, TypeVar
import openai
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel

from app.ai.providers.base import EmbeddingProvider, LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AIProviderError(Exception):
    """Base exception for AI provider call failures."""
    pass


class AIRateLimitError(AIProviderError):
    """Raised when an AI provider exceeds rate limits."""
    pass


class AITimeoutError(AIProviderError):
    """Raised when an AI provider request times out."""
    pass


class OpenAIProvider(LLMProvider, EmbeddingProvider):
    """Official OpenAI SDK provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model
        self._dimensions = embedding_dimensions
        self.timeout = timeout
        self.max_retries = max_retries

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=0,  # We manage bounded exponential retries explicitly
            )
        else:
            self.client = None

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.api_key and self.client)

    def _execute_with_retry(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a callable with bounded exponential backoff retries for transient errors."""
        if not self.client:
            raise AIProviderError("OpenAI client is not configured (missing OPENAI_API_KEY).")

        attempts = 0
        backoff = 1.0

        while True:
            try:
                attempts += 1
                return fn(*args, **kwargs)
            except RateLimitError as e:
                logger.warning("OpenAI rate limit encountered on attempt %d: %s", attempts, e)
                if attempts > self.max_retries:
                    raise AIRateLimitError(f"OpenAI rate limit exceeded after {attempts} attempts: {e}") from e
                time.sleep(backoff)
                backoff *= 2.0
            except (APITimeoutError, TimeoutError) as e:
                logger.warning("OpenAI timeout encountered on attempt %d: %s", attempts, e)
                if attempts > self.max_retries:
                    raise AITimeoutError(f"OpenAI request timed out after {attempts} attempts: {e}") from e
                time.sleep(backoff)
                backoff *= 2.0
            except (APIConnectionError, InternalServerError) as e:
                logger.warning("OpenAI connection/transient error on attempt %d: %s", attempts, e)
                if attempts > self.max_retries:
                    raise AIProviderError(f"OpenAI transient failure after {attempts} attempts: {e}") from e
                time.sleep(backoff)
                backoff *= 2.0
            except APIError as e:
                logger.error("OpenAI API error: %s", e)
                raise AIProviderError(f"OpenAI API error: {e}") from e
            except Exception as e:
                logger.error("Unexpected error calling OpenAI: %s", e)
                raise AIProviderError(f"Unexpected error calling OpenAI: {e}") from e

    def generate_structured_sync(
        self,
        schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> T:
        """Call OpenAI chat completions with structured output parsing against the given Pydantic schema."""
        def _call() -> T:
            response = self.client.beta.chat.completions.parse(
                model=kwargs.get("model", self.model),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=schema,
            )
            parsed = response.choices[0].message.parsed
            if parsed is None:
                raise AIProviderError("Model refused or returned empty structured content.")
            return parsed

        return self._execute_with_retry(_call)

    def generate_text_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> str:
        """Call OpenAI chat completions returning string narrative output."""
        def _call() -> str:
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or ""

        return self._execute_with_retry(_call)

    def embed_sync(
        self,
        texts: List[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Call OpenAI text-embedding endpoint returning float vectors."""
        if not texts:
            return []

        def _call() -> List[List[float]]:
            # Sanitize inputs (replace empty strings or newlines if any)
            cleaned = [t if t.strip() else " " for t in texts]
            response = self.client.embeddings.create(
                model=kwargs.get("model", self.embedding_model),
                input=cleaned,
            )
            # Maintain index order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        return self._execute_with_retry(_call)
