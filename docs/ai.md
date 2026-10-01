# Phase 7: AI Intelligence, Semantic Matching & LLM Understanding

## 1. Overview & Core Architectural Rule

Phase 7 introduces semantic AI capabilities to JobWatch AI while strictly preserving the **Phase 6 deterministic matching engine as the authoritative baseline**.

> **Critical Architecture Rule:**
> AI enhances understanding, but AI is never a single point of failure. If the LLM provider times out, fails, rate limits, or is disabled, JobWatch AI seamlessly produces deterministic match evaluations without HTTP 500 errors or application disruptions.

```text
                    JOB OPENING
                         │
                         ▼
                  Job Description
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   Deterministic                 AI Extraction
   Job Features                  & Normalization
          │                             │
          │                      ┌──────┴──────┐
          │                      ▼             ▼
          │                  Structured    Embeddings
          │                  Requirements      │
          │                      │             │
          └──────────────┬───────┘             │
                         │                     │
                         ▼                     ▼
                  Phase 6 Baseline       Cosine Similarity
                 Deterministic Score       Semantic Score
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                             Hybrid Matching
                       (0.70 Det + 0.30 Sem + Guardrails)
                                    │
                                    ▼
                           Enhanced Match Result
                                    │
                                    ▼
                             AI Explanation
                     (Score-Immutable Narrative)
```

---

## 2. AI Provider Abstraction

JobWatch AI decouples domain intelligence from third-party vendor APIs via an extensible provider layer in `app/ai/providers/`:

- **`LLMProvider` (Abstract Base Class)**:
  - `generate_structured_sync(schema, system_prompt, user_prompt, **kwargs) -> T`: Schema-enforced structured generation.
  - `generate_text_sync(system_prompt, user_prompt, **kwargs) -> str`: Freeform narrative generation.
  - `is_available() -> bool`: Provider availability check.

- **`EmbeddingProvider` (Abstract Base Class)**:
  - `embed_sync(texts: List[str], **kwargs) -> List[List[float]]`: Float vector generation.
  - `dimensions -> int`: Expected embedding dimension (default: 1536).
  - `is_available() -> bool`: Availability check.

- **`OpenAIProvider`**:
  - Official OpenAI Python SDK integration.
  - Chat completions with structured outputs via `client.beta.chat.completions.parse`.
  - Embeddings via `client.embeddings.create`.
  - Bounded exponential backoff retries (maximum 2 retries) handling transient `RateLimitError`, `APITimeoutError`, and `APIConnectionError`.
  - Explicit timeouts (default: 30.0s).

- **`FakeProvider`**:
  - Deterministic test provider for unit and CI execution without external API calls or credentials.
  - Produces schema-compliant structured data and reproducible unit-norm vector embeddings derived from text SHA-256 hashes.
  - Supports simulating rate limits and timeouts for resilience testing.

---

## 3. Structured Job Requirement Extraction

The extraction subsystem converts raw, unstructured job descriptions into structured qualifications:

### Schema (`AIJobRequirements`)
- `required_skills`: List[str] (mandatory skills).
- `preferred_skills`: List[str] (bonus/nice-to-have skills).
- `minimum_experience_years`: Optional[float] (years explicitly required).
- `maximum_experience_years`: Optional[float].
- `workplace_type`: Optional[str] (`REMOTE`, `HYBRID`, `ONSITE`).
- `employment_type`: Optional[str] (`FULL_TIME`, `CONTRACT`, etc.).
- `locations`: List[str].
- `minimum_salary`, `maximum_salary`, `salary_currency`: Explicit compensation info.
- `required_education_level`: Minimum academic degree.
- `role_keywords`: Domain keywords.
- `responsibilities`: Key job duties.

### Prompt Injection Defense
Job postings are untrusted third-party inputs. The user prompt wraps job descriptions inside `<JOB_DESCRIPTION>` tags:
```text
<JOB_DESCRIPTION>
{untrusted_content}
</JOB_DESCRIPTION>
```
System instructions instruct the model to treat everything inside the tags strictly as passive data and ignore embedded instructions attempting to alter system behavior.

### Caching & Invalidation
- Content hash: SHA-256 of `title + description + prompt_version`.
- If a cached extraction exists for `(job_id, input_hash, model, prompt_version)`, the database record is returned instantly with 0 LLM calls.
- If the job description changes, the `input_hash` changes, triggering re-extraction.
- Oversized descriptions (> 25,000 chars) are safely truncated before processing.

---

## 4. Vector Embeddings & Storage

### Storage
Embeddings are persisted in PostgreSQL using the `pgvector` extension:
- `job_embeddings`: Vector(1536), keyed by `job_id` and `content_hash`.
- `candidate_embeddings`: Vector(1536), keyed by `profile_id` and `content_hash`.

### PII Minimization
Candidate embedding representations strictly exclude private data:
- Excluded: passwords, password hashes, email addresses, phone numbers, tokens, database IDs.
- Included: headline, current role, target roles, verified skills, years of experience, workplace preferences, education level.

### Cosine Similarity Metric
Cosine similarity is computed via dot product of normalized L2 unit vectors:
$$\text{similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
Clamped to the range $[0.0, 1.0]$. The semantic score is scaled to $[0.0, 100.0]$.

---

## 5. Hybrid Scoring & Safety Guardrails

### Formula
The default transparent weighting combines deterministic and semantic signals:
$$\text{Hybrid Score} = (0.70 \times \text{Deterministic Score}) + (0.30 \times \text{Semantic Score})$$

### Hard Constraint Guardrails
High semantic similarity must never erase explicit disqualifications:
- **Workplace Mismatch**: If candidate preferences and job workplace are in explicit conflict (`status == "MISMATCH"`), the hybrid score is capped at `min(raw_hybrid, det_score + 10.0, 59.9)`.
- **Critical Skill / Experience Mismatch**: If required skills or experience are hard mismatches with 0 score, hybrid score is capped at `min(raw_hybrid, det_score + 15.0, 69.9)`.

### Graceful Fallbacks
- If semantic embeddings are unavailable (provider down or failed), `HybridMatcher` returns 100% of the deterministic score with `ai_status="AI_PARTIAL"`.
- If `AI_HYBRID_MATCHING_ENABLED=False`, deterministic score is returned with `ai_status="DISABLED"`.

---

## 6. Narrative AI Explanations

### Architecture
1. Deterministic code computes scores, matched skills, missing skills, and mismatches.
2. The structured match results are passed to the explanation generator.
3. The LLM produces a narrative structured response (`summary`, `strengths`, `gaps`, `recommendation`).
4. **Score Immutability**: The LLM never calculates or adjusts scores. The scores shown in the API are calculated by deterministic code.
5. **Deterministic Fallback**: If the LLM call fails or `AI_EXPLANATIONS_ENABLED=False`, a rule-based explanation template is returned without failing.

---

## 7. Database Migration

Migration `0006_ai_intelligence.py` adds:
- `CREATE EXTENSION IF NOT EXISTS vector;`
- `ai_job_extractions`
- `job_embeddings`
- `candidate_embeddings`
- `ai_explanations`

Downgrades cleanly remove all tables and indexes.

---

## 8. API Endpoints

### `POST /api/v1/matching/jobs/{job_id}/enhanced`
Evaluates hybrid match for the authenticated user and job.
- Response includes `deterministic_score`, `semantic_score`, `hybrid_score`, `ai_status`, `guardrail_applied`, `breakdown`, and `explanation`.

### `POST /api/v1/ai/jobs/{job_id}/extract`
Triggers or refreshes structured requirements extraction for a job.

### `GET /api/v1/ai/jobs/{job_id}/extraction`
Retrieves cached structured extraction for a job.
