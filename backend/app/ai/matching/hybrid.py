"""Hybrid matching combining deterministic Phase 6 scoring with semantic similarity."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from app.ai.config import DEFAULT_HYBRID_WEIGHTS, HYBRID_SCORING_VERSION, AIStatus
from app.matching.models import MatchResult


@dataclass
class HybridMatchOutcome:
    """Outcome of hybrid deterministic + semantic score synthesis."""

    deterministic_score: float
    semantic_score: Optional[float]
    semantic_similarity: Optional[float]
    hybrid_score: float
    weights: Dict[str, float]
    scoring_version: str
    ai_status: str
    guardrail_applied: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class HybridMatcher:
    """Combines deterministic matching baseline with semantic vector signals."""

    def __init__(
        self,
        deterministic_weight: float = 0.70,
        semantic_weight: float = 0.30,
    ) -> None:
        self.w_det = deterministic_weight
        self.w_sem = semantic_weight

    def combine(
        self,
        deterministic_result: MatchResult,
        semantic_data: Optional[Dict[str, Any]],
        ai_enabled: bool = True,
    ) -> HybridMatchOutcome:
        """Synthesize deterministic baseline and semantic signals with safety guardrails."""
        det_score = deterministic_result.score

        if not ai_enabled:
            return HybridMatchOutcome(
                deterministic_score=det_score,
                semantic_score=None,
                semantic_similarity=None,
                hybrid_score=det_score,
                weights={"deterministic": 1.0, "semantic": 0.0},
                scoring_version=HYBRID_SCORING_VERSION,
                ai_status=AIStatus.DISABLED.value,
            )

        if not semantic_data or "score" not in semantic_data:
            # Graceful fallback: 100% deterministic when semantic signal unavailable
            return HybridMatchOutcome(
                deterministic_score=det_score,
                semantic_score=None,
                semantic_similarity=None,
                hybrid_score=det_score,
                weights={"deterministic": 1.0, "semantic": 0.0},
                scoring_version=HYBRID_SCORING_VERSION,
                ai_status=AIStatus.AI_PARTIAL.value,
                details={"reason": "Semantic similarity unavailable; fallback to deterministic baseline."},
            )

        sem_score = float(semantic_data["score"])
        sem_sim = float(semantic_data.get("similarity", sem_score / 100.0))

        raw_hybrid = round(det_score * self.w_det + sem_score * self.w_sem, 1)

        # Safety Guardrails: Hard Constraints
        # Check if critical deterministic dimensions are hard MISMATCHes
        breakdown = deterministic_result.breakdown or {}
        workplace_mismatch = breakdown.get("workplace", {}).get("status") == "MISMATCH"
        skills_mismatch = (
            breakdown.get("skills", {}).get("status") == "MISMATCH"
            and breakdown.get("skills", {}).get("score", 0.0) == 0.0
        )
        exp_mismatch = breakdown.get("experience", {}).get("status") == "MISMATCH"

        guardrail_applied = False
        final_score = raw_hybrid

        # If a critical constraint is explicitly violated, cap hybrid score so semantic
        # similarity cannot artificially inflate an incompatible candidate to a strong match
        if workplace_mismatch or (skills_mismatch and exp_mismatch):
            final_score = min(raw_hybrid, det_score + 10.0, 59.9)
            guardrail_applied = True
        elif skills_mismatch or exp_mismatch:
            final_score = min(raw_hybrid, det_score + 15.0, 69.9)
            guardrail_applied = True

        final_score = round(max(0.0, min(100.0, final_score)), 1)

        return HybridMatchOutcome(
            deterministic_score=det_score,
            semantic_score=sem_score,
            semantic_similarity=sem_sim,
            hybrid_score=final_score,
            weights={"deterministic": self.w_det, "semantic": self.w_sem},
            scoring_version=HYBRID_SCORING_VERSION,
            ai_status=AIStatus.AI_AVAILABLE.value,
            guardrail_applied=guardrail_applied,
            details={
                "raw_hybrid_score": raw_hybrid,
                "breakdown": breakdown,
            },
        )
