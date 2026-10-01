"""Tests for semantic similarity calculation and hybrid score combination with guardrails."""

import pytest
from app.ai.config import AIStatus
from app.ai.matching.hybrid import HybridMatcher
from app.ai.matching.semantic import SemanticMatcher
from app.matching.models import MatchResult


def test_semantic_matcher_compare_vectors():
    """Verify SemanticMatcher scales cosine similarity to 0-100 score."""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    res_identical = SemanticMatcher.compare_vectors(vec1, vec2)
    assert res_identical is not None
    assert res_identical["similarity"] == 1.0
    assert res_identical["score"] == 100.0

    vec_ortho = [0.0, 1.0, 0.0]
    res_ortho = SemanticMatcher.compare_vectors(vec1, vec_ortho)
    assert res_ortho is not None
    assert res_ortho["similarity"] == 0.0
    assert res_ortho["score"] == 0.0

    # None handling
    assert SemanticMatcher.compare_vectors(None, vec1) is None
    assert SemanticMatcher.compare_vectors(vec1, None) is None


def test_hybrid_matcher_standard_combination():
    """Verify 70/30 deterministic and semantic score weighting."""
    matcher = HybridMatcher(deterministic_weight=0.70, semantic_weight=0.30)

    mock_match = MatchResult(
        job_id="00000000-0000-0000-0000-000000000001",
        profile_id="00000000-0000-0000-0000-000000000002",
        score=80.0,
        confidence="HIGH",
        scoring_version="v1",
        breakdown={
            "skills": {"score": 80.0, "status": "MATCH"},
            "experience": {"score": 80.0, "status": "MATCH"},
            "workplace": {"score": 100.0, "status": "MATCH"},
        },
    )

    semantic_data = {"score": 70.0, "similarity": 0.70}
    outcome = matcher.combine(mock_match, semantic_data)

    # 80.0 * 0.70 + 70.0 * 0.30 = 56.0 + 21.0 = 77.0
    assert outcome.deterministic_score == 80.0
    assert outcome.semantic_score == 70.0
    assert outcome.hybrid_score == 77.0
    assert outcome.ai_status == AIStatus.AI_AVAILABLE.value
    assert outcome.guardrail_applied is False


def test_hybrid_matcher_fallback_when_semantic_unavailable():
    """Verify fallback to 100% deterministic score when semantic vector fails."""
    matcher = HybridMatcher()
    mock_match = MatchResult(
        job_id="00000000-0000-0000-0000-000000000001",
        profile_id="00000000-0000-0000-0000-000000000002",
        score=82.5,
        confidence="HIGH",
        scoring_version="v1",
        breakdown={},
    )

    outcome = matcher.combine(mock_match, semantic_data=None)

    assert outcome.hybrid_score == 82.5
    assert outcome.semantic_score is None
    assert outcome.ai_status == AIStatus.AI_PARTIAL.value


def test_hybrid_matcher_disabled_flag():
    """Verify deterministic baseline is preserved when AI matching is disabled."""
    matcher = HybridMatcher()
    mock_match = MatchResult(
        job_id="00000000-0000-0000-0000-000000000001",
        profile_id="00000000-0000-0000-0000-000000000002",
        score=75.0,
        confidence="HIGH",
        scoring_version="v1",
        breakdown={},
    )

    outcome = matcher.combine(mock_match, semantic_data={"score": 95.0}, ai_enabled=False)

    assert outcome.hybrid_score == 75.0
    assert outcome.semantic_score is None
    assert outcome.ai_status == AIStatus.DISABLED.value


def test_hybrid_matcher_guardrail_caps_workplace_mismatch():
    """Verify hard workplace mismatch triggers guardrail cap despite high semantic similarity."""
    matcher = HybridMatcher(deterministic_weight=0.70, semantic_weight=0.30)

    # Candidate has low deterministic score due to hard workplace mismatch
    mock_match = MatchResult(
        job_id="00000000-0000-0000-0000-000000000001",
        profile_id="00000000-0000-0000-0000-000000000002",
        score=40.0,
        confidence="HIGH",
        scoring_version="v1",
        breakdown={
            "workplace": {"score": 0.0, "status": "MISMATCH"},
            "skills": {"score": 90.0, "status": "MATCH"},
        },
    )

    # But high semantic similarity of 95.0 (raw hybrid would be 40*0.7 + 95*0.3 = 56.5)
    semantic_data = {"score": 95.0, "similarity": 0.95}
    outcome = matcher.combine(mock_match, semantic_data)

    assert outcome.guardrail_applied is True
    # Capped at min(raw_hybrid, det_score + 10.0, 59.9) = min(56.5, 50.0, 59.9) = 50.0
    assert outcome.hybrid_score <= 50.0
