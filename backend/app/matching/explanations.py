"""Deterministic human-readable explanation generator."""

from typing import Dict, List, Tuple

from app.matching.models import DimensionResult, DimensionStatus


def generate_explanations(
    dimension_results: Dict[str, DimensionResult],
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Synthesize matched criteria, missing criteria, mismatches, and structured reasons.

    Every reason is deterministically generated from dimension evaluation outputs.
    """
    all_matched: List[str] = []
    all_missing: List[str] = []
    all_mismatches: List[str] = []
    all_reasons: List[str] = []

    for dim_name, result in dimension_results.items():
        if result.matched:
            all_matched.extend(result.matched)
        if result.missing:
            all_missing.extend(result.missing)
        if result.mismatches:
            all_mismatches.extend(result.mismatches)
        if result.reasons:
            all_reasons.extend(result.reasons)

    # De-duplicate while preserving insertion order
    def dedupe(items: List[str]) -> List[str]:
        seen = set()
        res = []
        for x in items:
            if x not in seen:
                seen.add(x)
                res.append(x)
        return res

    return (
        dedupe(all_matched),
        dedupe(all_missing),
        dedupe(all_mismatches),
        dedupe(all_reasons),
    )
