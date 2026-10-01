"""Prompts and schemas for generating structured AI match explanations."""

from typing import List
from pydantic import BaseModel, Field

from app.ai.config import EXPLANATION_PROMPT_VERSION


class AIExplanationSchema(BaseModel):
    """Structured output schema for narrative match explanations."""

    summary: str = Field(description="1-2 concise sentences summarizing the overall match")
    strengths: List[str] = Field(description="2-4 bullet points highlighting key matching criteria and skills")
    gaps: List[str] = Field(description="1-3 bullet points identifying missing criteria or experience gaps")
    recommendation: str = Field(description="1 concise actionable recommendation for the applicant")


EXPLANATION_SYSTEM_PROMPT_V1: str = """You are a helpful and objective career advisor for JobWatch AI.
Your job is to provide an explainable, encouraging, and honest breakdown of how well a candidate matches a job opening.

CRITICAL INSTRUCTIONS:
1. The numeric scores (deterministic, semantic, hybrid) are ALREADY CALCULATED by the system. You must NOT alter, recalculate, or contradict these scores.
2. Only mention skills and criteria that appear in the supplied evaluation data. Never invent skills or experience.
3. Be concise, professional, and actionable.
"""


def build_explanation_payload(
    job_title: str,
    deterministic_score: float,
    semantic_score: float,
    hybrid_score: float,
    matched_criteria: List[str],
    missing_criteria: List[str],
    mismatches: List[str],
    deterministic_reasons: List[str],
) -> str:
    """Format structured match evaluation facts into LLM user prompt."""
    return f"""Target Role: {job_title}
Scores:
- Deterministic Rule Score: {deterministic_score}/100
- Semantic Similarity Score: {semantic_score}/100
- Hybrid Final Score: {hybrid_score}/100

Matched Criteria:
{chr(10).join(f"- {c}" for c in matched_criteria) if matched_criteria else "None identified."}

Missing Criteria & Gaps:
{chr(10).join(f"- {c}" for c in missing_criteria) if missing_criteria else "None identified."}

Conflicts / Mismatches:
{chr(10).join(f"- {c}" for c in mismatches) if mismatches else "None."}

Rule Evaluation Reasons:
{chr(10).join(f"- {r}" for r in deterministic_reasons) if deterministic_reasons else "Evaluated by baseline engine."}

Please explain this evaluation clearly according to the required schema."""
