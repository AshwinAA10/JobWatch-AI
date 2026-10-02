# Phase 13: AI Operational Guide

## 1. AI Configuration
The AI subsystem is governed by environment variables in `.env` and `app/core/config.py`:

```env
# AI Engine Configuration
OPENAI_API_KEY=sk-...                  # Empty triggers FakeProvider fallback
OPENAI_MODEL=gpt-4o-mini               # Primary structured extraction model
OPENAI_EMBEDDING_MODEL=text-embedding-3-small # 1536-dim vector model
AI_EXTRACTION_ENABLED=true             # Master toggle for LLM job parsing
AI_EMBEDDING_ENABLED=true              # Master toggle for vector embedding generation
AI_HYBRID_MATCHING_ENABLED=true        # Master toggle for semantic hybrid scoring
AI_EXPLANATIONS_ENABLED=true           # Master toggle for AI explanation generation
```

---

## 2. Telemetry, Usage & Cost Monitoring
All AI provider invocations and cache hits are recorded by the in-memory `AICostTracker` singleton (`app/ai/cost/tracker.py`).

### Telemetry Endpoint
- **URL**: `GET /api/v1/ai/telemetry/cost`
- **Access**: Authenticated candidates and system administrators
- **Metrics Tracked**:
  - `total_calls`: Total AI provider calls executed
  - `total_tokens`: Total tokens consumed across models
  - `total_estimated_cost_usd`: Estimated cumulative expenditure
  - `cache_hit_rate`: Ratio of cache hits vs misses
  - `models`: Per-model breakdown of input, output, and cost

---

## 3. Resiliency & Outage Playbook

### Scenario A: OpenAI Provider Downtime / Rate Limiting (429 / 5xx)
1. The system logs an AI warning with operation context.
2. In-flight requests fall back gracefully to deterministic rule-based matching (Phase 6).
3. `FakeProvider` generates deterministic pseudo-embeddings when credentials are absent or during local development.
4. Core job ingestion, user registration, application tracking, and notifications remain 100% operational.

### Scenario B: Embedding Model Upgrades
When transitioning embedding models (e.g. from `text-embedding-3-small` to a newer version):
1. Increment `EMBEDDING_VERSION` (e.g., `v1` -> `v2`).
2. Do not mix disparate vector spaces: queries must compare against vectors produced by the identical model and version.
3. Use version-aware filtering when running cosine similarity scans.

### Scenario C: High Token Consumption Alert
1. Inspect `GET /api/v1/ai/telemetry/cost` to identify the runaway operation.
2. If job extraction is consuming excessive tokens, verify that job descriptions are truncated to the configured maximum length (e.g., 4000 characters) before sending to the LLM.
3. Verify that cache hits are increasing for duplicate jobs.
