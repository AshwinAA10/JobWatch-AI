# Phase 13: Advanced AI & Semantic Intelligence Architecture

## 1. Overview
Phase 13 elevates JobWatch AI from initial baseline LLM extraction (Phase 7) into a layered Semantic Intelligence system. The architecture guarantees deterministic guardrails, explainable evidence generation, skill ontology mapping with alias normalization, natural language vector retrieval, interaction-aware ranking, and strict cost controls.

```text
                    JOBWATCH AI
                         │
          ┌──────────────┴──────────────┐
          │                             │
        Jobs                         Users
          │                             │
          ▼                             ▼
   Job Understanding            Candidate Understanding
          │                             │
          └──────────────┬──────────────┘
                         ▼
                  Skill Ontology
                         │
                         ▼
                   Embeddings
                         │
                         ▼
              Semantic Retrieval
                         │
                         ▼
                Hybrid Matching
                         │
                         ▼
              Personalized Ranking
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       Explainability          Recommendations
             │                       │
             └───────────┬───────────┘
                         ▼
                    User Actions
                         │
                         ▼
                  Feedback Signals
                         │
                         ▼
              Interaction Adaptation
```

---

## 2. Core Architectural Pillars

### A. Provider Abstraction
- All LLM and embedding operations are encapsulated behind the `LLMProvider` and `EmbeddingProvider` abstract interfaces in `app/ai/providers/base.py`.
- Two concrete implementations exist:
  - `OpenAIProvider`: Handles GPT-4o-mini structured output and text-embedding-3-small vectors.
  - `FakeProvider`: Deterministic fallback for local development, offline operation, and automated CI test execution.
- Direct external API vendor imports in route controllers or repository layers are strictly prohibited.

### B. Skill Ontology & Normalization
- Located in `app/ai/ontology/`.
- **Normalization**: Maps diverse technology aliases (e.g. `js`, `reactjs`, `k8s`, `postgres`, `golang`) to canonical names (`JavaScript`, `React`, `Kubernetes`, `PostgreSQL`, `Go`).
- **Semantic Relationships**: Categorizes skills and specifies directed, weighted transferability (e.g., `Python` transfers to `FastAPI` with weight 0.85; `Docker` transfers to `Kubernetes` with weight 0.70).
- **Skill Gap Analysis**: Compares candidate skills against job requirements, isolating exact matches, transferable matches, and missing criteria with calculated requirement coverage.

### C. Semantic Retrieval & Search
- Located in `app/ai/search/service.py`.
- Transforms natural language queries into 1536-dimensional embeddings.
- Executes vector cosine similarity against all active job embeddings in PostgreSQL (`JobEmbedding`).
- Combines vector proximity with hard structured filters (`workplace_type`, `location`).

### D. Interaction-Aware Personalized Ranking
- Located in `app/ai/ranking/service.py`.
- Ingests user interaction signals (applications, bookmarks, target job titles, preferred workplace types).
- Bounded scoring adjustment:
  - Applied jobs receive a `-20.0` demotion to prevent cluttering discovery feeds.
  - Bookmarked jobs receive a `+8.0` engagement boost.
  - Profile preferences add `+5.0` bonuses for matching titles, locations, and workplace formats.
  - Scores are strictly bounded between `0.0` and `100.0`.

### E. Evidence-Backed Explainability
- Never relies on ungrounded generative free-text.
- Explanations decompose into structured evidence categories:
  - Exact skill matches (`matched_required`).
  - Transferable skills detected via ontology.
  - Remaining skill gaps.
  - Location and workplace preference alignment.

---

## 3. Data Flow Pipelines

### Job Analysis Pipeline
```text
Job Ingestion -> Ingestion Normalization -> AI Job Extraction -> Validated Schema Persistence -> Embedding Generation (Version v1) -> Vector Storage
```

### Candidate Gap Analysis Pipeline
```text
Candidate Profile & Skills -> Deterministic Canonicalization -> Comparison with Job Requirements -> Ontology Transferability Check -> Gap Breakdown & Coverage Score
```
