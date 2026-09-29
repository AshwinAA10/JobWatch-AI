"""Weighted scoring and dynamic normalization for missing data."""

from typing import Dict, Tuple

from app.matching.constants import DEFAULT_MATCH_WEIGHTS
from app.matching.models import DimensionResult, DimensionStatus


def validate_weights(weights: Dict[str, float]) -> bool:
    """Ensure dimension weights sum to exactly 1.0 within floating tolerance."""
    total = sum(weights.values())
    return abs(total - 1.0) < 1e-5


def calculate_weighted_score(
    dimension_results: Dict[str, DimensionResult],
    weights: Dict[str, float] = None,
) -> Tuple[float, str, Dict[str, float]]:
    """Compute normalized weighted aggregate score and confidence.

    Missing or inapplicable dimensions (status UNKNOWN or NOT_APPLICABLE with score=None)
    are removed from the denominator and the score is normalized over available dimensions.
    """
    applied_weights = weights or DEFAULT_MATCH_WEIGHTS

    available_weight_sum = 0.0
    weighted_score_accum = 0.0
    effective_contributions: Dict[str, float] = {}

    for dim_name, result in dimension_results.items():
        weight = applied_weights.get(dim_name, 0.0)
        if result.score is not None:
            available_weight_sum += weight
            weighted_score_accum += result.score * weight
            effective_contributions[dim_name] = round(result.score * weight, 2)

    if available_weight_sum > 0:
        normalized_score = weighted_score_accum / available_weight_sum
    else:
        normalized_score = 0.0

    final_score = round(normalized_score, 1)

    # Confidence based on percentage of available evaluation weight
    if available_weight_sum >= 0.70:
        confidence = "HIGH"
    elif available_weight_sum >= 0.40:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return final_score, confidence, effective_contributions
