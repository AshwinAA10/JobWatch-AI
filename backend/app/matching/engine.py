"""Pure deterministic matching engine."""

from typing import Dict, Optional

from app.matching.constants import DEFAULT_MATCH_WEIGHTS, SCORING_VERSION
from app.matching.explanations import generate_explanations
from app.matching.models import (
    CandidateMatchFeatures,
    DimensionResult,
    JobMatchFeatures,
    MatchResult,
)
from app.matching.rules import (
    evaluate_education,
    evaluate_employment_type,
    evaluate_experience,
    evaluate_location,
    evaluate_salary,
    evaluate_skills,
    evaluate_title,
    evaluate_workplace,
)
from app.matching.scoring import calculate_weighted_score, validate_weights


class MatchingEngine:
    """Orchestrates deterministic matching across all feature dimensions."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize with custom or default dimension weights."""
        self.weights = weights or DEFAULT_MATCH_WEIGHTS
        if not validate_weights(self.weights):
            raise ValueError(f"Matching weights must sum to 1.0 (current sum: {sum(self.weights.values())})")

    def match(
        self,
        candidate: CandidateMatchFeatures,
        job: JobMatchFeatures,
    ) -> MatchResult:
        """Execute deterministic matching between candidate features and job features.

        This function is pure and free of side effects.
        """
        # 1. Evaluate all 8 dimensions
        dimension_results: Dict[str, DimensionResult] = {
            "skills": evaluate_skills(candidate, job),
            "experience": evaluate_experience(candidate, job),
            "title": evaluate_title(candidate, job),
            "location": evaluate_location(candidate, job),
            "workplace": evaluate_workplace(candidate, job),
            "employment_type": evaluate_employment_type(candidate, job),
            "salary": evaluate_salary(candidate, job),
            "education": evaluate_education(candidate, job),
        }

        # 2. Compute aggregate normalized weighted score
        score, confidence, contributions = calculate_weighted_score(
            dimension_results,
            self.weights,
        )

        # 3. Generate structured deterministic explanations
        matched_criteria, missing_criteria, mismatches, reasons = generate_explanations(
            dimension_results,
        )

        # 4. Assemble breakdown dictionary
        breakdown = {
            dim_name: result.to_dict()
            for dim_name, result in dimension_results.items()
        }

        return MatchResult(
            job_id=job.job_id,
            profile_id=candidate.profile_id,
            score=score,
            confidence=confidence,
            scoring_version=SCORING_VERSION,
            breakdown=breakdown,
            matched_criteria=matched_criteria,
            missing_criteria=missing_criteria,
            mismatches=mismatches,
            reasons=reasons,
            metadata={
                "contributions": contributions,
                "weights_used": self.weights,
            },
        )
