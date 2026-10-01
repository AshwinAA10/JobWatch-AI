"""Deterministic mock email provider for unit and integration testing."""

from dataclasses import dataclass
from typing import List, Optional
import uuid

from app.notifications.payload import DeliveryResult
from app.notifications.providers.base import EmailProvider


@dataclass
class SentEmailRecord:
    """Record of an email dispatched via FakeEmailProvider."""

    to_email: str
    subject: str
    text_body: str
    html_body: Optional[str]
    recipient_name: Optional[str]
    message_id: str


class FakeEmailProvider(EmailProvider):
    """In-memory mock email provider that records calls without sending real emails."""

    def __init__(
        self,
        should_fail: bool = False,
        failure_type: str = "transient",  # "transient" or "permanent"
        error_message: Optional[str] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        self.should_fail = should_fail
        self.failure_type = failure_type
        self.error_message = error_message or ("Mock SMTP timeout" if failure_type == "transient" else "Mock invalid recipient")
        self.retry_after = retry_after
        self.sent_messages: List[SentEmailRecord] = []

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> DeliveryResult:
        """Simulate email sending."""
        if self.should_fail:
            return DeliveryResult(
                success=False,
                error_message=self.error_message,
                is_transient=(self.failure_type == "transient"),
                retry_after_seconds=self.retry_after,
            )

        msg_id = f"fake-msg-{uuid.uuid4().hex[:8]}"
        self.sent_messages.append(
            SentEmailRecord(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                recipient_name=recipient_name,
                message_id=msg_id,
            )
        )
        return DeliveryResult(
            success=True,
            provider_message_id=msg_id,
        )

    def clear(self) -> None:
        """Clear recorded messages."""
        self.sent_messages.clear()
