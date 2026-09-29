# Phase 6: Deterministic Job Matching Engine

## 1. Overview & Objective

The **JobWatch AI Matching Engine (Phase 6)** is a pure deterministic, explainable, testable system designed to answer:
> *"How well does this candidate's structured profile match this job?"*

Phase 6 forms the **deterministic baseline** for candidate-job relevance. It implements strict rules and scoring across 8 dimensions without reliance on non-deterministic LLMs, vector embeddings, or machine learning models.

```text
                 CandidateProfile
                        │
                        ▼
            Candidate Match Features
                        │
                        ▼
                Matching Engine  ◄── Job Match Features ◄── Job (+ JobRequirements)
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
  Component Scores              Explanations
          │                           │
          └─────────────┬─────────────┘
                        ▼
             Normalized Weighted Score
                        │
                        ▼
                   MatchResult
                        │
                        ▼
                Phase 7 AI Baseline
```

---

## 2. The 8 Evaluation Dimensions

Matching evaluates 8 distinct dimensions when criteria and candidate data are present:

| Dimension | Default Weight | Description & Deterministic Logic |
| :--- | :--- | :--- |
| **Skills** | **35%** | Evaluates required skills (80% component weight) and preferred skills (20% component weight). Deterministic alias normalization (e.g. `ReactJS` $\to$ `react`). |
| **Experience** | **20%** | Compares candidate years of experience against `minimum_experience_years` and `maximum_experience_years`. Excess experience is treated conservatively rather than as a hard mismatch. |
| **Job Title / Desired Role** | **15%** | Deterministic token overlap, alias normalization (`engineer` $\leftrightarrow$ `developer`), and substring matching between desired roles and job title. |
| **Location** | **10%** | Matches candidate preferred city, state, country, or relocation willingness against job location. Fully remote jobs automatically score 100%. |
| **Workplace Type** | **10%** | Compares `REMOTE`, `HYBRID`, or `ONSITE` preferences against job workplace classification. |
| **Employment Type** | **5%** | Evaluates arrangements (`FULL_TIME`, `PART_TIME`, `CONTRACT`, `INTERNSHIP`, `TEMPORARY`). |
| **Salary** | **3%** | Compares candidate minimum/maximum expectations with job bounds. Currencies must match; incompatible currencies yield `UNKNOWN` without artificial conversion rates. |
| **Education** | **2%** | Compares degrees against explicit requirements using a deterministic 5-tier academic hierarchy (`High School` < `Associate` < `Bachelor's` < `Master's` < `Doctorate`). |

---

## 3. Dynamic Normalization & Missing Data Strategy

### Core Principle: Missing Data $\neq$ Mismatch

In the real world, job postings and candidate profiles have incomplete metadata. A candidate should never be penalized simply because a job posting did not publish a salary band or minimum years of experience.

Each dimension evaluates to one of five explicit statuses:
- `MATCH`: Criteria satisfied.
- `PARTIAL`: Criteria partially satisfied (e.g. slight experience gap, partial skill coverage, willing to relocate).
- `MISMATCH`: Criteria explicitly contradicted.
- `UNKNOWN`: Data missing from candidate or job.
- `NOT_APPLICABLE`: Dimension not required for this role (e.g. no education or experience requirement).

### Score Normalization Formula

Dimensions with `UNKNOWN` or `NOT_APPLICABLE` outcomes yield `score = None` and are **dynamically removed from the denominator**:

$$\text{Final Score} = \frac{\sum_{d \in \text{Available}} (\text{Score}_d \times \text{Weight}_d)}{\sum_{d \in \text{Available}} \text{Weight}_d}$$

**Example:**
If a job specifies skills and workplace type, but leaves salary and education empty:
- Available dimensions: Skills (0.35), Workplace (0.10).
- Sum of available weights: $0.35 + 0.10 = 0.45$.
- If both dimensions score 100%, the normalized score is:
  $$\frac{100 \times 0.35 + 100 \times 0.10}{0.45} = 100.0$$
- Result is not unfairly compressed down to 45.0.

Confidence is determined by total available weight:
- $\ge 70\%$: `HIGH`
- $\ge 40\%$: `MEDIUM`
- $< 40\%$: `LOW`

---

## 4. Engineering Score Bands

Score bands are provided as engineering interpretation signals, not guarantees:

- **80.0 – 100.0**: `STRONG_MATCH`
- **60.0 – 79.99**: `MODERATE_MATCH`
- **40.0 – 59.99**: `WEAK_MATCH`
- **0.0 – 39.99**: `POOR_MATCH`

---

## 5. Persistence Layer

Two tables support the matching system:

1. **`job_requirements`**:
   - Stores structured role requirements (`required_skills`, `preferred_skills`, `minimum_experience_years`, `maximum_experience_years`, `minimum_salary`, `maximum_salary`, `salary_currency`, `required_education_level`).
   - Foreign key to `jobs.id` with `UNIQUE` constraint.

2. **`job_matches`**:
   - Stores computed match evaluation (`user_id`, `profile_id`, `job_id`, `score`, `scoring_version="v1"`, `breakdown`, `matched_criteria`, `missing_criteria`, `mismatches`, `reasons`, `calculated_at`).
   - Unique constraint on `(profile_id, job_id)`.
   - Indexed on `(profile_id, score)` and `(job_id, score)` for fast ranking.

---

## 6. REST API Endpoints

All endpoints require standard Bearer token authentication and operate strictly on the authenticated user's profile:

- `POST /api/v1/matching/jobs/{job_id}?persist=true`
  - Runs deterministic matching between candidate profile and job.
  - Persists and returns `JobMatchResponse`.
- `GET /api/v1/matching/jobs/{job_id}`
  - Retrieves previously calculated match for user.
- `GET /api/v1/matching/matches?min_score=60.0&skip=0&limit=50`
  - Lists calculated matches for user ordered by score descending.
- `PUT /api/v1/matching/jobs/{job_id}/requirements`
  - Sets or updates structured requirements for a job opening.
- `GET /api/v1/matching/jobs/{job_id}/requirements`
  - Retrieves structured requirements for a job opening.

---

## 7. Phase 7 Interface Contract

Phase 6 provides the deterministic foundation. Phase 7 can augment without altering Phase 6:
- Consume `MatchResult` as a baseline input.
- Enhance title matching through semantic embeddings.
- Add skill taxonomy inference (e.g. `Django` $\implies$ `Python`).
- Augment explanations with LLM-generated summaries while preserving deterministic component scores.
