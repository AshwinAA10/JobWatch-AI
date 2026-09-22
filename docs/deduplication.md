# JobWatch AI — Deduplication & Job Identity (Phase 4)

The **Deduplication & Job Identity Engine** resolves job identity across disparate company portals and Applicant Tracking Systems (Greenhouse, Lever, Workday, career sites), links equivalent postings to a single canonical job representation, prevents false-positive merges, and **never deletes duplicate source records**.

---

## 1. Core Architectural Principle

Phase 4 preserves all discovered records and establishes directed relationships:

```text
Canonical Job (Parent)
      │
      ├── Duplicate Posting A (e.g. Greenhouse)
      ├── Duplicate Posting B (e.g. Lever)
      └── Duplicate Posting C (e.g. Regional Portal)
```

### Critical Rules
1. **Never Delete Duplicate Jobs**: Every source record is kept intact in PostgreSQL. Deleting duplicates destroys external application links, provenance, timestamp discovery history, and source reliability metrics.
2. **Precision Before Recall**: When evidence is ambiguous or contradictory, **do not merge**. A false negative leaves an extra job record visible; a false positive erroneously consolidates distinct requisitions or experience levels.
3. **No AI / No LLM Classification**: Deduplication is 100% deterministic (token Jaccard, sequence matching, seniority parsing, rule-based URL and ID equality, hard company boundaries). Embeddings and LLMs are strictly deferred to Phase 7/13.

---

## 2. Multi-Layer Identity Model

Job identity is separated into three distinct layers:

### Layer 1: Source Identity
- **Composite Key**: `(career_source_id, external_id)`
- Enforced at the database level via unique constraint `uq_jobs_source_external_id`.
- Guarantees that re-polling the same career board never produces duplicate rows for the same external requisition.

### Layer 2: Canonical Identity
- **Representation**: `jobs.canonical_job_id` (nullable self-referencing foreign key).
- Identifies the authoritative real-world opening.
- If `canonical_job_id` is `NULL`, the job is an independent or canonical root record.
- If `canonical_job_id` is set, it points directly to the canonical root record.

### Layer 3: Duplicate Relationship
- **Entity**: `JobDuplicate` table.
- Stores the directed pair `(canonical_job_id, duplicate_job_id)` with confidence score (0.0 to 1.0), match type enum, structured `matched_fields` JSON, and explainable `reason` text.

---

## 3. Matching Pipeline

```text
                     ┌──────────────────┐
                     │   Fetched Job    │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  Candidate Query │ (Same Company, Lookback Window, Max Candidates)
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Hard Invariants  │ (Company Boundary, Self-Match Guard)
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │   Exact Checks   │ (Application URL = 1.0, Source URL = 0.98)
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Similarity Score │ (Title, Location, Workplace, Employment, Description)
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Confidence Check │
                     └────────┬─────────┘
          ┌───────────────────┼───────────────────┐
          │ >= 0.90           │ 0.75 - 0.89       │ < 0.75
          ▼                   ▼                   ▼
     ┌───────────┐      ┌───────────┐       ┌───────────┐
     │ HIGH CONF │      │  MEDIUM   │       │    LOW    │
     │ Link Dup  │      │ Candidate │       │ Separate  │
     │ Keep Both │      │ Keep Both │       │ Keep Both │
     └───────────┘      └───────────┘       └───────────┘
```

1. **Candidate Blocking**:
   - Queries candidates with `company_id == job.company_id` (jobs from different companies are never compared).
   - Constrained by `DEDUP_LOOKBACK_DAYS` (default: 90 days) and bounded by `DEDUP_MAX_CANDIDATES` (default: 100).
   - Prevents $O(N^2)$ global database scans.

2. **Hard Contradiction Gates**:
   - Different company $\rightarrow$ score = 0.0 (`DIFFERENT_COMPANY`).
   - Seniority conflict (e.g. Intern vs Senior/Staff/Manager) $\rightarrow$ score penalized to $\le 0.10$ (`CONTRADICTION`).
   - Physical city conflict on on-site postings (e.g. London vs Tokyo) $\rightarrow$ score penalized to $\le 0.15$ (`CONTRADICTION`).

3. **Exact Signals**:
   - Exact normalized application URL equality $\rightarrow$ score = 1.0 (`EXACT_APPLICATION_URL`).
   - Exact normalized source URL equality $\rightarrow$ score = 0.98 (`EXACT_SOURCE_URL`).

4. **Weighted Similarity Model**:
   - Weights:
     - `title`: 0.45
     - `location`: 0.20
     - `workplace_type`: 0.15
     - `employment_type`: 0.10
     - `description`: 0.10
   - Title similarity combines token Jaccard and sequence matching ratio.
   - Description similarity guards against false positives: template boilerplate overlap cannot trigger high confidence if titles diverge.

---

## 4. Deterministic Canonical Selection

When two jobs are identified as duplicates, canonical root selection follows a strict deterministic hierarchy:

1. **Established Root Preference**: If one job is already an established canonical root (no `canonical_job_id`), it is chosen as canonical.
2. **Earliest Discovery**: The job with the earlier `first_seen_at` timestamp is chosen as canonical.
3. **Metadata Completeness**: If timestamps are identical, the job with more complete fields (description, application URL, location, workplace type) is selected.
4. **Stable Tie-Breaker**: Lexicographical comparison of UUID strings.

### Canonical Cycle & Chaining Prevention
Chaining (`A -> B -> C`) is strictly prevented by resolving the root canonical before persisting. If Job C matches duplicate Job B, `resolve_canonical_root(B)` traverses to Root A, resulting in `B -> A` and `C -> A`.

---

## 5. Configuration Reference

| Variable | Type | Default | Description |
|---|---|---|---|
| `DEDUP_ENABLED` | `bool` | `true` | Enable/disable automatic deduplication |
| `DEDUP_HIGH_THRESHOLD` | `float` | `0.90` | Score threshold for automatic duplicate linking |
| `DEDUP_MEDIUM_THRESHOLD` | `float` | `0.75` | Threshold for review candidate classification |
| `DEDUP_MAX_CANDIDATES` | `int` | `100` | Max candidates evaluated per job |
| `DEDUP_LOOKBACK_DAYS` | `int` | `90` | Candidate search historical window |

---

## 6. Deduplication API

Endpoints under `/api/v1/dedup`:

- `GET /api/v1/dedup/status`: Returns operational configuration and threshold bounds.
- `GET /api/v1/dedup/duplicates`: Query duplicate relationships with optional `canonical_id` filter and pagination.
- `POST /api/v1/dedup/run/{job_id}`: Trigger on-demand deduplication analysis for a specific job ID.
