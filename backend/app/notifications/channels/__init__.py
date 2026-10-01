"""Channel exports for notifications dispatch."""

from app.notifications.channels.base import NotificationChannel
from app.notifications.channels.email import EmailChannel
from app.notifications.channels.webhook import WebhookChannel

__all__ = [
    "NotificationChannel",
    "EmailChannel",
    "WebhookChannel",
]
