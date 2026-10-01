"""Notification templates package."""

from app.notifications.templates.email_match import render_match_email
from app.notifications.templates.webhook_match import render_match_webhook_payload

__all__ = [
    "render_match_email",
    "render_match_webhook_payload",
]
