"""Base provider interfaces for LLM execution and Embedding generation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface for LLM completions and structured outputs."""

    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        return True

    @abstractmethod
    def generate_structured_sync(
        self,
        schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> T:
        """Generate schema-constrained structured output synchronously."""
        pass

    @abstractmethod
    def generate_text_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> str:
        """Generate narrative text completion synchronously."""
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding generation."""

    @abstractmethod
    def embed_sync(
        self,
        texts: List[str],
        **kwargs: Any,
    ) -> List[List[float]]:
        """Generate float vector embeddings for input text strings synchronously."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Expected dimension length of generated embeddings."""
        pass
