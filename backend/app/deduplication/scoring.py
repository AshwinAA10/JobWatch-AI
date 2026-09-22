"""Deterministic similarity scoring algorithms and false-positive protection."""

from difflib import SequenceMatcher
import re
from typing import Dict, Optional, Set, Tuple
from app.models.job import Job
from app.models.job_duplicate import MatchType
from app.deduplication.normalizers import (
    clean_text,
    extract_seniority,
    normalize_location,
    normalize_title,
    normalize_url,
)
from app.deduplication.schemas import MatchResult

DEFAULT_WEIGHTS = {
    "title": 0.45,
    "location": 0.20,
    "workplace_type": 0.15,
    "employment_type": 0.10,
    "description": 0.10,
}

# Stopwords to filter from descriptions
BASIC_STOPWORDS: Set[str] = {
    "the", "and", "a", "an", "in", "on", "at", "to", "for", "of", "with",
    "is", "are", "as", "by", "this", "that", "it", "from", "or", "be",
    "will", "can", "have", "has", "we", "you", "our", "your", "all", "about",
}


def jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Calculate Jaccard similarity coefficient between two token sets."""
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return float(intersection / union) if union > 0 else 0.0


def tokenize(text: str) -> Set[str]:
    """Tokenize normalized text into unique word stems/tokens, filtering out stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
    return {w for w in words if w not in BASIC_STOPWORDS}


def calculate_title_similarity(title_a: str, title_b: str) -> Tuple[float, Optional[str]]:
    """Calculate title similarity combining token Jaccard and string sequence ratio.
    
    Returns (score, seniority_conflict_reason).
    """
    norm_a = normalize_title(title_a)
    norm_b = normalize_title(title_b)

    if norm_a == norm_b:
        return 1.0, None

    # Check seniority alignment
    sen_a = extract_seniority(title_a)
    sen_b = extract_seniority(title_b)

    # Hard seniority contradiction: intern vs experienced/manager/lead
    intern_tiers = {"intern"}
    senior_tiers = {"senior", "staff", "lead", "principal", "manager", "director"}
    if (sen_a in intern_tiers and sen_b in senior_tiers) or (sen_b in intern_tiers and sen_a in senior_tiers):
        return 0.10, f"Seniority contradiction: '{sen_a}' vs '{sen_b}'"

    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    jaccard = jaccard_similarity(tokens_a, tokens_b)
    seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()

    combined = (0.5 * jaccard) + (0.5 * seq_ratio)

    # Moderate penalty if seniorities are distinct
    if sen_a and sen_b and sen_a != sen_b:
        combined = min(combined, 0.60)
        return combined, f"Distinct seniority levels: '{sen_a}' vs '{sen_b}'"

    return combined, None


def calculate_location_similarity(loc_a: Optional[str], loc_b: Optional[str]) -> float:
    """Evaluate location compatibility between two postings."""
    norm_a = normalize_location(loc_a)
    norm_b = normalize_location(loc_b)

    if not norm_a or not norm_b:
        return 1.0  # Missing location does not penalize

    if norm_a == norm_b:
        return 1.0

    # If either is remote, flexible match
    if "remote" in norm_a or "remote" in norm_b:
        return 0.85

    # Check city token intersection
    tokens_a = set(norm_a.split(","))
    tokens_b = set(norm_b.split(","))
    if tokens_a.intersection(tokens_b):
        return 0.90

    # Contradictory physical locations
    return 0.0


def calculate_workplace_similarity(type_a: Optional[str], type_b: Optional[str]) -> float:
    """Evaluate workplace type compatibility (remote, hybrid, on-site)."""
    if not type_a or not type_b:
        return 1.0
    a = type_a.lower().strip()
    b = type_b.lower().strip()
    if a == b:
        return 1.0
    if ("remote" in a and "on-site" in b) or ("on-site" in a and "remote" in b):
        return 0.0
    return 0.50


def calculate_employment_similarity(type_a: Optional[str], type_b: Optional[str]) -> float:
    """Evaluate employment classification (full-time, part-time, contract, internship)."""
    if not type_a or not type_b:
        return 1.0
    a = type_a.lower().strip()
    b = type_b.lower().strip()
    if a == b:
        return 1.0
    if ("intern" in a and "full" in b) or ("full" in a and "intern" in b):
        return 0.0
    return 0.50


def calculate_description_similarity(desc_a: Optional[str], desc_b: Optional[str], title_score: float) -> float:
    """Evaluate description similarity, guarded against template reuse false positives."""
    if not desc_a or not desc_b:
        return 0.80  # Neutral when descriptions are absent

    tokens_a = tokenize(clean_text(desc_a))
    tokens_b = tokenize(clean_text(desc_b))

    if not tokens_a or not tokens_b:
        return 0.80

    raw_jaccard = jaccard_similarity(tokens_a, tokens_b)

    # Section 54 False-Positive Protection:
    # High template similarity alone must not create high confidence if titles differ significantly
    if title_score < 0.70 and raw_jaccard > 0.75:
        return 0.40

    return raw_jaccard


def calculate_url_similarity(url_a: Optional[str], url_b: Optional[str]) -> Tuple[float, bool]:
    """Check normalized URL equality. Returns (score, is_exact_match)."""
    norm_a = normalize_url(url_a)
    norm_b = normalize_url(url_b)

    if norm_a and norm_b and norm_a == norm_b:
        return 1.0, True

    if not norm_a or not norm_b:
        return 0.50, False  # Neutral when missing

    return 0.0, False


def evaluate_job_pair(
    job_a: Job,
    job_b: Job,
    high_threshold: float = 0.90,
    medium_threshold: float = 0.75,
) -> MatchResult:
    """Evaluate duplicate confidence between two jobs using deterministic and weighted rules.
    
    Hard constraints (Company boundary, self-match) are enforced first before any scoring.
    """
    # 1. Prevent self-matching
    if job_a.id == job_b.id:
        return MatchResult(
            score=0.0,
            match_type="SELF_MATCH",
            matched_fields={},
            reason="Cannot evaluate job against itself",
        )

    # 2. Hard Company Boundary (Section 33)
    if job_a.company_id != job_b.company_id:
        return MatchResult(
            score=0.0,
            match_type="DIFFERENT_COMPANY",
            matched_fields={},
            reason="Different companies cannot be duplicate postings",
        )

    # 3. Exact Source Identity Check (already handled in DB by composite key)
    if (
        job_a.career_source_id == job_b.career_source_id
        and job_a.external_id
        and job_a.external_id == job_b.external_id
    ):
        return MatchResult(
            score=1.0,
            match_type=MatchType.EXACT_EXTERNAL_ID.value,
            matched_fields={"external_id": 1.0},
            reason="Identical career source and external ID",
        )

    # 4. Exact Application URL Check (Section 18, 22)
    url_score, is_exact_app_url = calculate_url_similarity(
        job_a.application_url,
        job_b.application_url,
    )
    if is_exact_app_url:
        return MatchResult(
            score=1.0,
            match_type=MatchType.EXACT_APPLICATION_URL.value,
            matched_fields={"application_url": 1.0},
            reason="Exact normalized application URL match across postings",
        )

    # 5. Exact Source URL Check (Section 19, 22)
    _, is_exact_src_url = calculate_url_similarity(job_a.source_url, job_b.source_url)
    if is_exact_src_url:
        return MatchResult(
            score=0.98,
            match_type=MatchType.EXACT_SOURCE_URL.value,
            matched_fields={"source_url": 0.98},
            reason="Exact normalized source URL match across postings",
        )

    # 6. Component Similarity Evaluation
    title_score, seniority_conflict = calculate_title_similarity(job_a.title, job_b.title)
    if seniority_conflict and "Seniority contradiction" in seniority_conflict:
        return MatchResult(
            score=0.10,
            match_type="CONTRADICTION",
            matched_fields={"title": title_score},
            reason=seniority_conflict,
        )

    loc_score = calculate_location_similarity(job_a.location, job_b.location)
    workplace_score = calculate_workplace_similarity(job_a.workplace_type, job_b.workplace_type)
    emp_score = calculate_employment_similarity(job_a.employment_type, job_b.employment_type)
    desc_score = calculate_description_similarity(job_a.description, job_b.description, title_score)

    matched_fields = {
        "title": round(title_score, 3),
        "location": round(loc_score, 3),
        "workplace_type": round(workplace_score, 3),
        "employment_type": round(emp_score, 3),
        "description": round(desc_score, 3),
    }

    # Hard physical location contradiction penalty: on-site roles in distinct cities
    is_a_remote = bool(job_a.workplace_type and "remote" in job_a.workplace_type.lower())
    is_b_remote = bool(job_b.workplace_type and "remote" in job_b.workplace_type.lower())
    if loc_score == 0.0 and not is_a_remote and not is_b_remote:
        return MatchResult(
            score=0.15,
            match_type="CONTRADICTION",
            matched_fields=matched_fields,
            reason="Conflicting physical locations for on-site/non-remote positions",
        )

    # Weighted composite score
    total_weight = sum(DEFAULT_WEIGHTS.values())
    raw_score = sum(matched_fields[k] * DEFAULT_WEIGHTS[k] for k in DEFAULT_WEIGHTS)
    final_score = round(raw_score / total_weight, 3)

    # Determine classification
    if final_score >= high_threshold:
        match_type = MatchType.HIGH_CONFIDENCE.value
        reason = (
            f"High confidence duplicate (score: {final_score:.2f}). "
            f"Title: {title_score:.2f}, Loc: {loc_score:.2f}, Workplace: {workplace_score:.2f}"
        )
    elif final_score >= medium_threshold:
        match_type = MatchType.MEDIUM_CONFIDENCE.value
        reason = (
            f"Medium confidence match (score: {final_score:.2f}) requiring manual verification. "
            f"Title: {title_score:.2f}, Loc: {loc_score:.2f}"
        )
    else:
        match_type = "LOW_CONFIDENCE"
        reason = f"Low confidence match (score: {final_score:.2f}) below threshold"

    return MatchResult(
        score=final_score,
        match_type=match_type,
        matched_fields=matched_fields,
        reason=reason,
    )
