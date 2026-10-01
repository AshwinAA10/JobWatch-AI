"""Base notification channel interface."""

from abc import ABC, abstractmethod

from app.notifications.payload import DeliveryResult, NotificationPayload


class NotificationChannel(ABC):
    """Abstract interface for dispatch channels."""

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Channel identifier string (e.g. 'EMAIL', 'WEBHOOK')."""
        pass

    @abstractmethod
    def send(self, payload: NotificationPayload) -> DeliveryResult:
        """Execute delivery for the given notification payload synchronously."""
        pass
