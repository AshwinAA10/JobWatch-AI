"""Webhook payload templates for job match notifications."""

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID
from app.notifications.config import WEBHOOK_PAYLOAD_VERSION


def render_match_webhook_payload(
    event_type: str,
    notification_id: UUID,
    profile_id: UUID,
    job_data: Dict[str, Any],
    match_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Structure clean outbound JSON webhook payload."""
    return {
        "event_type": event_type,
        "payload_version": WEBHOOK_PAYLOAD_VERSION,
        "notification_id": str(notification_id),
        "candidate_id": str(profile_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "job": {
            "id": str(job_data.get("id")),
            "title": job_data.get("title"),
            "company": job_data.get("company_name"),
            "location": job_data.get("location"),
            "workplace_type": job_data.get("workplace_type"),
            "employment_type": job_data.get("employment_type"),
            "application_url": job_data.get("application_url"),
        },
        "match": {
            "score": match_data.get("score"),
            "scoring_version": match_data.get("scoring_version", "v1"),
            "confidence": match_data.get("confidence"),
            "matched_criteria": match_data.get("matched_criteria", []),
            "missing_criteria": match_data.get("missing_criteria", []),
            "summary": match_data.get("explanation", {}).get("summary") if isinstance(match_data.get("explanation"), dict) else None,
        },
    }
