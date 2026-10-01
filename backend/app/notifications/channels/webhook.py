"""Webhook notification channel dispatching JSON payloads via WebhookProvider."""

import logging
from typing import Optional

from app.notifications.channels.base import NotificationChannel
from app.notifications.payload import DeliveryResult, NotificationPayload
from app.notifications.providers.base import WebhookProvider
from app.notifications.templates.webhook_match import render_match_webhook_payload

logger = logging.getLogger(__name__)


class WebhookChannel(NotificationChannel):
    """Webhook notification channel structuring JSON payloads and dispatching via WebhookProvider."""

    def __init__(self, provider: WebhookProvider) -> None:
        self.provider = provider

    @property
    def channel_name(self) -> str:
        return "WEBHOOK"

    def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Validate destination URL, structure payload, and dispatch via provider."""
        if not payload.webhook_url:
            logger.error("notification.webhook.missing_url notification_id=%s", payload.notification_id)
            return DeliveryResult(
                success=False,
                error_message="Candidate has no webhook URL configured.",
                is_transient=False,
            )

        webhook_data = render_match_webhook_payload(
            event_type=payload.event_type,
            notification_id=payload.notification_id,
            profile_id=payload.profile_id,
            job_data=payload.job_data,
            match_data=payload.match_data,
        )

        return self.provider.send_webhook(
            url=payload.webhook_url,
            payload=webhook_data,
            secret=payload.webhook_secret,
        )
