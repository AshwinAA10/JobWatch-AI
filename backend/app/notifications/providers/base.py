"""Base provider interfaces for email and webhook transport."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.notifications.payload import DeliveryResult


class EmailProvider(ABC):
    """Abstract interface for email dispatch providers."""

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> DeliveryResult:
        """Send an email message synchronously."""
        pass


class WebhookProvider(ABC):
    """Abstract interface for webhook dispatch providers."""

    @abstractmethod
    def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        """Deliver a webhook payload synchronously."""
        pass
