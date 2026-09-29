"""Deterministic matching evaluation rules for individual dimensions."""

import re
from typing import List, Optional, Set

from app.matching.constants import (
    EDUCATION_HIERARCHY,
    PREFERRED_SKILL_WEIGHT,
    REQUIRED_SKILL_WEIGHT,
)
from app.matching.features import normalize_title
from app.matching.models import (
    CandidateMatchFeatures,
    DimensionResult,
    DimensionStatus,
    JobMatchFeatures,
)


def evaluate_skills(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate skill overlap between candidate and job requirements."""
    req_skills = job.required_skills
    pref_skills = job.preferred_skills

    if not req_skills and not pref_skills:
        return DimensionResult(
            dimension="skills",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["No skill requirements specified for this job."],
        )

    matched_req = sorted(list(candidate.skills.intersection(req_skills)))
    missing_req = sorted(list(req_skills - candidate.skills))
    matched_pref = sorted(list(candidate.skills.intersection(pref_skills)))
    missing_pref = sorted(list(pref_skills - candidate.skills))

    matched_all = sorted(list(set(matched_req + matched_pref)))
    missing_all = sorted(list(set(missing_req + missing_pref)))

    req_cov = len(matched_req) / len(req_skills) if req_skills else 1.0
    pref_cov = len(matched_pref) / len(pref_skills) if pref_skills else 1.0

    if req_skills and pref_skills:
        score = (req_cov * REQUIRED_SKILL_WEIGHT + pref_cov * PREFERRED_SKILL_WEIGHT) * 100.0
    elif req_skills:
        score = req_cov * 100.0
    else:
        score = pref_cov * 100.0

    score = round(score, 1)

    reasons: List[str] = []
    if req_skills:
        reasons.append(f"Matched {len(matched_req)} of {len(req_skills)} required skills.")
    if pref_skills:
        reasons.append(f"Matched {len(matched_pref)} of {len(pref_skills)} preferred skills.")

    if score >= 90.0 or (req_skills and len(missing_req) == 0):
        status = DimensionStatus.MATCH
    elif score >= 40.0 or (req_skills and len(matched_req) > 0):
        status = DimensionStatus.PARTIAL
    else:
        status = DimensionStatus.MISMATCH

    return DimensionResult(
        dimension="skills",
        score=score,
        status=status,
        matched=matched_all,
        missing=missing_all,
        mismatches=missing_req,
        reasons=reasons,
        metadata={
            "required_coverage": round(req_cov, 2),
            "preferred_coverage": round(pref_cov, 2) if pref_skills else None,
            "required_skills_count": len(req_skills),
            "preferred_skills_count": len(pref_skills),
        },
    )


def evaluate_experience(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate candidate experience years against job minimum/maximum experience requirements."""
    min_exp = job.minimum_experience_years
    max_exp = job.maximum_experience_years

    if min_exp is None and max_exp is None:
        return DimensionResult(
            dimension="experience",
            score=None,
            status=DimensionStatus.NOT_APPLICABLE,
            reasons=["No experience range requirement specified for this job."],
        )

    cand_exp = candidate.total_experience_years
    if cand_exp is None:
        return DimensionResult(
            dimension="experience",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate total experience is not specified."],
        )

    reasons: List[str] = []
    matched: List[str] = []
    missing: List[str] = []
    mismatches: List[str] = []

    # Check minimum experience requirement
    if min_exp is not None:
        if cand_exp >= min_exp:
            score = 100.0
            status = DimensionStatus.MATCH
            reasons.append(f"Candidate meets minimum experience requirement ({cand_exp:.1f} >= {min_exp:.1f} years).")
            matched.append(f"Minimum experience ({min_exp:.1f} years)")
        else:
            ratio = cand_exp / min_exp if min_exp > 0 else 0.0
            if ratio >= 0.7:
                score = 70.0
                status = DimensionStatus.PARTIAL
                reasons.append(f"Candidate has {cand_exp:.1f} years experience, slightly below required {min_exp:.1f} years.")
            elif ratio >= 0.4:
                score = 40.0
                status = DimensionStatus.PARTIAL
                reasons.append(f"Candidate has {cand_exp:.1f} years experience, moderately below required {min_exp:.1f} years.")
            else:
                score = 15.0
                status = DimensionStatus.MISMATCH
                reasons.append(f"Candidate experience ({cand_exp:.1f} years) is significantly below required {min_exp:.1f} years.")
                mismatches.append(f"Below minimum experience ({cand_exp:.1f} < {min_exp:.1f} years)")
            missing.append(f"Required experience gap ({min_exp - cand_exp:.1f} years)")
    else:
        score = 100.0
        status = DimensionStatus.MATCH

    # Check maximum experience conservatively
    if max_exp is not None and cand_exp > max_exp:
        excess = cand_exp - max_exp
        if excess > 5.0:
            score = min(score, 80.0)
            reasons.append(f"Candidate experience ({cand_exp:.1f} years) exceeds preferred maximum of {max_exp:.1f} years.")
        else:
            reasons.append(f"Candidate experience slightly exceeds preferred maximum of {max_exp:.1f} years (treated conservatively).")

    return DimensionResult(
        dimension="experience",
        score=score,
        status=status,
        matched=matched,
        missing=missing,
        mismatches=mismatches,
        reasons=reasons,
        metadata={
            "candidate_experience_years": cand_exp,
            "job_min_experience": min_exp,
            "job_max_experience": max_exp,
        },
    )


def evaluate_title(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate job title match against candidate's desired or current roles."""
    if not job.title:
        return DimensionResult(
            dimension="title",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Job title is missing."],
        )

    job_title_norm = normalize_title(job.title)
    candidate_roles = list(candidate.desired_titles)
    if candidate.current_title and candidate.current_title not in candidate_roles:
        candidate_roles.append(candidate.current_title)

    if not candidate_roles:
        return DimensionResult(
            dimension="title",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate has not specified desired roles or current title."],
        )

    best_score = 0.0
    best_role = ""
    job_tokens = set(job_title_norm.split())

    for role in candidate_roles:
        role_norm = normalize_title(role)
        if role_norm == job_title_norm:
            best_score = 100.0
            best_role = role
            break

        # Substring containment
        if role_norm in job_title_norm or job_title_norm in role_norm:
            if best_score < 90.0:
                best_score = 90.0
                best_role = role
            continue

        # Token overlap
        role_tokens = set(role_norm.split())
        overlap = job_tokens.intersection(role_tokens)
        if overlap:
            overlap_ratio = len(overlap) / max(len(job_tokens), len(role_tokens))
            calc_score = round(overlap_ratio * 80.0, 1)
            if calc_score > best_score:
                best_score = calc_score
                best_role = role

    reasons: List[str] = []
    matched: List[str] = []
    mismatches: List[str] = []

    if best_score >= 85.0:
        status = DimensionStatus.MATCH
        reasons.append(f"Job title aligns strongly with candidate target role '{best_role}'.")
        matched.append(f"Target role: {best_role}")
    elif best_score >= 40.0:
        status = DimensionStatus.PARTIAL
        reasons.append(f"Partial title overlap between '{job.title}' and candidate role '{best_role}'.")
        matched.append(f"Partial role match: {best_role}")
    else:
        status = DimensionStatus.MISMATCH
        reasons.append(f"Job title '{job.title}' does not closely align with candidate desired roles.")
        mismatches.append(f"Title divergence: {job.title}")

    return DimensionResult(
        dimension="title",
        score=best_score,
        status=status,
        matched=matched,
        mismatches=mismatches,
        reasons=reasons,
        metadata={"matched_role": best_role, "normalized_job_title": job_title_norm},
    )


def evaluate_location(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate location compatibility including remote preference and relocation."""
    # Remote workplace check
    job_workplace = (job.workplace_type or "").upper().replace("-", "_")
    if job_workplace == "REMOTE":
        return DimensionResult(
            dimension="location",
            score=100.0,
            status=DimensionStatus.MATCH,
            matched=["Remote job eliminates geographic constraints."],
            reasons=["Job is fully remote."],
        )

    if not job.location:
        return DimensionResult(
            dimension="location",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Job location is unspecified."],
        )

    job_loc_norm = job.location.strip().lower()
    candidate_locations = [loc.strip().lower() for loc in candidate.preferred_locations if loc]
    if candidate.city:
        candidate_locations.append(candidate.city.lower())

    if not candidate_locations and not candidate.willing_to_relocate:
        return DimensionResult(
            dimension="location",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate has not specified location preferences or residence."],
        )

    # Direct match or containment
    is_direct_match = any(
        loc in job_loc_norm or job_loc_norm in loc for loc in candidate_locations
    )

    if is_direct_match:
        return DimensionResult(
            dimension="location",
            score=100.0,
            status=DimensionStatus.MATCH,
            matched=[f"Location match: {job.location}"],
            reasons=[f"Job location '{job.location}' matches candidate preferred location."],
        )

    # Relocation allowance
    if candidate.willing_to_relocate:
        return DimensionResult(
            dimension="location",
            score=75.0,
            status=DimensionStatus.PARTIAL,
            matched=["Relocation acceptable"],
            reasons=[f"Job in '{job.location}' differs from preferred cities, but candidate is willing to relocate."],
            metadata={"willing_to_relocate": True},
        )

    return DimensionResult(
        dimension="location",
        score=0.0,
        status=DimensionStatus.MISMATCH,
        mismatches=[f"Location mismatch: {job.location}"],
        reasons=[f"Job location '{job.location}' does not match candidate preferences and candidate is not open to relocation."],
    )


def evaluate_workplace(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate workplace type compatibility (REMOTE, HYBRID, ONSITE)."""
    if not job.workplace_type:
        return DimensionResult(
            dimension="workplace",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Job workplace type is unspecified."],
        )

    job_wp = job.workplace_type.strip().upper().replace("-", "_").replace(" ", "_")
    cand_wps = [wp.strip().upper().replace("-", "_").replace(" ", "_") for wp in candidate.workplace_types if wp]

    if not cand_wps:
        return DimensionResult(
            dimension="workplace",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate has no workplace type preference."],
        )

    # Normalize aliases
    alias_map = {"ON_SITE": "ONSITE"}
    job_wp_canon = alias_map.get(job_wp, job_wp)
    cand_wps_canon = {alias_map.get(wp, wp) for wp in cand_wps}

    if job_wp_canon in cand_wps_canon:
        return DimensionResult(
            dimension="workplace",
            score=100.0,
            status=DimensionStatus.MATCH,
            matched=[f"Workplace type: {job_wp_canon}"],
            reasons=[f"Job workplace type ({job_wp_canon}) matches candidate preference."],
        )

    return DimensionResult(
        dimension="workplace",
        score=0.0,
        status=DimensionStatus.MISMATCH,
        mismatches=[f"Workplace type: {job_wp_canon}"],
        reasons=[f"Job workplace type ({job_wp_canon}) does not match candidate preferences ({', '.join(cand_wps_canon)})."],
    )


def evaluate_employment_type(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate employment type compatibility (FULL_TIME, CONTRACT, etc.)."""
    if not job.employment_type:
        return DimensionResult(
            dimension="employment_type",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Job employment type is unspecified."],
        )

    job_et = job.employment_type.strip().upper().replace("-", "_").replace(" ", "_")
    cand_ets = [et.strip().upper().replace("-", "_").replace(" ", "_") for et in candidate.employment_types if et]

    if not cand_ets:
        return DimensionResult(
            dimension="employment_type",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate has no employment type preferences specified."],
        )

    if job_et in cand_ets:
        return DimensionResult(
            dimension="employment_type",
            score=100.0,
            status=DimensionStatus.MATCH,
            matched=[f"Employment type: {job_et}"],
            reasons=[f"Job employment type ({job_et}) matches candidate preferences."],
        )

    return DimensionResult(
        dimension="employment_type",
        score=0.0,
        status=DimensionStatus.MISMATCH,
        mismatches=[f"Employment type: {job_et}"],
        reasons=[f"Job employment type ({job_et}) does not match candidate preferences ({', '.join(cand_ets)})."],
    )


def evaluate_salary(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate compensation alignment between candidate expectations and job range."""
    job_min = job.minimum_salary
    job_max = job.maximum_salary
    job_curr = job.salary_currency

    cand_min = candidate.minimum_salary
    cand_max = candidate.maximum_salary
    cand_curr = candidate.salary_currency

    if job_min is None and job_max is None:
        return DimensionResult(
            dimension="salary",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Job salary information is not specified."],
        )

    if cand_min is None and cand_max is None:
        return DimensionResult(
            dimension="salary",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate salary expectations are not specified."],
        )

    if job_curr and cand_curr and job_curr.upper() != cand_curr.upper():
        return DimensionResult(
            dimension="salary",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=[f"Incompatible salary currencies ({job_curr} vs {cand_curr}); conversion is not performed in Phase 6."],
        )

    # Job range lower bound vs candidate expectations
    effective_job_max = job_max if job_max is not None else job_min
    effective_job_min = job_min if job_min is not None else job_max

    if cand_min is not None and effective_job_max is not None and effective_job_max < cand_min:
        gap = cand_min - effective_job_max
        gap_ratio = gap / cand_min
        if gap_ratio <= 0.10:
            return DimensionResult(
                dimension="salary",
                score=50.0,
                status=DimensionStatus.PARTIAL,
                mismatches=[f"Slight salary gap ({gap} below candidate minimum)"],
                reasons=[f"Job maximum ({effective_job_max}) is slightly below candidate minimum ({cand_min})."],
            )
        return DimensionResult(
            dimension="salary",
            score=0.0,
            status=DimensionStatus.MISMATCH,
            mismatches=[f"Job maximum ({effective_job_max}) is below candidate minimum ({cand_min})"],
            reasons=[f"Job salary offering is below candidate minimum requirement."],
        )

    # Overlap or meeting minimum
    return DimensionResult(
        dimension="salary",
        score=100.0,
        status=DimensionStatus.MATCH,
        matched=["Salary range meets candidate expectations."],
        reasons=["Job salary satisfies candidate minimum requirements."],
        metadata={
            "job_min": job_min,
            "job_max": job_max,
            "candidate_min": cand_min,
            "candidate_max": cand_max,
        },
    )


def evaluate_education(candidate: CandidateMatchFeatures, job: JobMatchFeatures) -> DimensionResult:
    """Evaluate education level requirement against candidate qualifications."""
    req_edu = job.required_education_level
    if not req_edu:
        return DimensionResult(
            dimension="education",
            score=None,
            status=DimensionStatus.NOT_APPLICABLE,
            reasons=["No education requirement specified for this job."],
        )

    cand_edu = candidate.highest_education_level
    if not cand_edu and not candidate.degrees:
        return DimensionResult(
            dimension="education",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=["Candidate education qualifications are not specified."],
        )

    # Normalize and rank
    def get_rank(edu_str: str) -> int:
        clean = edu_str.lower().strip()
        for key, rank in EDUCATION_HIERARCHY.items():
            if key in clean:
                return rank
        return 0

    req_rank = get_rank(req_edu)
    cand_rank = get_rank(cand_edu) if cand_edu else 0
    for deg in candidate.degrees:
        cand_rank = max(cand_rank, get_rank(deg))

    if req_rank == 0:
        return DimensionResult(
            dimension="education",
            score=None,
            status=DimensionStatus.UNKNOWN,
            reasons=[f"Unrecognized education requirement '{req_edu}'."],
        )

    if cand_rank >= req_rank:
        return DimensionResult(
            dimension="education",
            score=100.0,
            status=DimensionStatus.MATCH,
            matched=[f"Education requirement met: {req_edu}"],
            reasons=[f"Candidate satisfies education requirement ({req_edu})."],
        )

    if cand_rank == req_rank - 1:
        return DimensionResult(
            dimension="education",
            score=50.0,
            status=DimensionStatus.PARTIAL,
            missing=[f"Education level below {req_edu}"],
            reasons=[f"Candidate education is one tier below preferred requirement ({req_edu})."],
        )

    return DimensionResult(
        dimension="education",
        score=0.0,
        status=DimensionStatus.MISMATCH,
        mismatches=[f"Education level below {req_edu}"],
        reasons=[f"Candidate qualifications do not satisfy required education level ({req_edu})."],
    )
