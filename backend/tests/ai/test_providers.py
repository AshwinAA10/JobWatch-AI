"""Tests for AI provider abstractions and implementations."""

import pytest
from openai import RateLimitError
from app.ai.providers.fake_provider import FakeProvider
from app.ai.providers.openai_provider import (
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    OpenAIProvider,
)
from app.schemas.ai import AIJobRequirements


def test_fake_provider_structured_output():
    """Verify FakeProvider produces schema-compliant structured output."""
    provider = FakeProvider()
    prompt = "Extract requirements for a Senior Python Developer with 5+ years experience and FastAPI"

    result = provider.generate_structured_sync(
        schema=AIJobRequirements,
        system_prompt="system",
        user_prompt=prompt,
    )

    assert isinstance(result, AIJobRequirements)
    assert "Python" in result.required_skills
    assert result.minimum_experience_years == 3.0
    assert result.workplace_type in ["REMOTE", "HYBRID", "ONSITE"]
    assert provider.call_count_structured == 1


def test_fake_provider_embeddings_reproducibility():
    """Verify FakeProvider returns deterministic unit-norm vectors of correct dimension."""
    provider = FakeProvider(dimensions=1536)
    text1 = "Senior Python Engineer with Cloud experience"
    text2 = "Senior Python Engineer with Cloud experience"
    text3 = "Junior Graphic Designer"

    vectors1 = provider.embed_sync([text1])
    vectors2 = provider.embed_sync([text2])
    vectors3 = provider.embed_sync([text3])

    assert len(vectors1) == 1
    assert len(vectors1[0]) == 1536
    # Exact reproducibility for identical text
    assert vectors1[0] == vectors2[0]
    # Different text yields different vector
    assert vectors1[0] != vectors3[0]

    # Check unit norm (length ~ 1.0)
    norm = sum(x * x for x in vectors1[0]) ** 0.5
    assert abs(norm - 1.0) < 1e-4
    assert provider.call_count_embed == 3


def test_fake_provider_empty_input():
    """Verify FakeProvider handles empty text gracefully."""
    provider = FakeProvider(dimensions=1536)
    vectors = provider.embed_sync([""])
    assert len(vectors) == 1
    assert len(vectors[0]) == 1536


def test_fake_provider_simulated_failures():
    """Verify FakeProvider can simulate rate limits and timeouts for testing."""
    fail_rate = FakeProvider(should_fail=True, failure_type="rate_limit")
    with pytest.raises(AIRateLimitError, match="Simulated OpenAI rate limit"):
        fail_rate.generate_structured_sync(AIJobRequirements, "system", "prompt")

    fail_timeout = FakeProvider(should_fail=True, failure_type="timeout")
    with pytest.raises(AITimeoutError, match="Simulated OpenAI timeout"):
        fail_timeout.embed_sync(["text"])


def test_openai_provider_initialization():
    """Verify OpenAIProvider initializes with custom parameters and handles missing API key."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini", embedding_model="text-embedding-3-small")
    assert provider.model == "gpt-4o-mini"
    assert provider.embedding_model == "text-embedding-3-small"
    assert provider.is_available() is True

    empty_provider = OpenAIProvider(api_key="", model="gpt-4o-mini")
    assert empty_provider.is_available() is False


def test_openai_provider_not_configured_raises():
    """Verify calling an unconfigured OpenAIProvider raises AIProviderError."""
    empty_provider = OpenAIProvider(api_key="")
    with pytest.raises(AIProviderError, match="OpenAI client is not configured"):
        empty_provider.generate_structured_sync(AIJobRequirements, "sys", "user")

    with pytest.raises(AIProviderError, match="OpenAI client is not configured"):
        empty_provider.embed_sync(["text"])
