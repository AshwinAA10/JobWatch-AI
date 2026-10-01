"""Deterministic mock webhook provider for unit and integration testing."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import uuid

from app.notifications.payload import DeliveryResult
from app.notifications.providers.base import WebhookProvider


@dataclass
class SentWebhookRecord:
    """Record of a webhook dispatched via FakeWebhookProvider."""

    url: str
    payload: Dict[str, Any]
    secret: Optional[str]
    delivery_id: str


class FakeWebhookProvider(WebhookProvider):
    """In-memory mock webhook provider tracking dispatches without making network requests."""

    def __init__(
        self,
        should_fail: bool = False,
        failure_type: str = "transient",  # "transient" or "permanent"
        status_code: int = 503,
        error_message: Optional[str] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        self.should_fail = should_fail
        self.failure_type = failure_type
        self.status_code = status_code
        self.error_message = error_message or f"Mock webhook HTTP {status_code}"
        self.retry_after = retry_after
        self.sent_webhooks: List[SentWebhookRecord] = []

    def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        """Simulate webhook dispatch."""
        if self.should_fail:
            return DeliveryResult(
                success=False,
                error_message=self.error_message,
                is_transient=(self.failure_type == "transient"),
                retry_after_seconds=self.retry_after,
            )

        delivery_id = f"hook-{uuid.uuid4().hex[:8]}"
        self.sent_webhooks.append(
            SentWebhookRecord(
                url=url,
                payload=payload,
                secret=secret,
                delivery_id=delivery_id,
            )
        )
        return DeliveryResult(
            success=True,
            provider_message_id=delivery_id,
        )

    def clear(self) -> None:
        """Clear recorded webhooks."""
        self.sent_webhooks.clear()
