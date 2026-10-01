"""Email notification channel dispatching via configured EmailProvider."""

import logging
from typing import Optional

from app.notifications.channels.base import NotificationChannel
from app.notifications.payload import DeliveryResult, NotificationPayload
from app.notifications.providers.base import EmailProvider
from app.notifications.templates.email_match import render_match_email

logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel):
    """Email notification channel rendering structured templates and dispatching via EmailProvider."""

    def __init__(self, provider: EmailProvider) -> None:
        self.provider = provider

    @property
    def channel_name(self) -> str:
        return "EMAIL"

    def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Validate recipient email, render templates, and dispatch via provider."""
        if not payload.recipient_email:
            logger.error("notification.email.missing_recipient notification_id=%s", payload.notification_id)
            return DeliveryResult(
                success=False,
                error_message="Candidate has no verified recipient email address.",
                is_transient=False,
            )

        subject, text_body, html_body = render_match_email(
            job_data=payload.job_data,
            match_data=payload.match_data,
            recipient_name=payload.recipient_name,
        )

        return self.provider.send_email(
            to_email=payload.recipient_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            recipient_name=payload.recipient_name,
        )
