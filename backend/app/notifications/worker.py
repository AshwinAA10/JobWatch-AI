"""Background worker for multi-channel notification delivery with atomic claiming and retries."""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.candidate_profile import CandidateProfile
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.notification_preference import NotificationPreference
from app.notifications.channels.base import NotificationChannel
from app.notifications.channels.email import EmailChannel
from app.notifications.channels.webhook import WebhookChannel
from app.notifications.config import (
    DeliveryStatus,
    NotificationChannelType,
    NotificationStatus,
)
from app.notifications.payload import DeliveryResult, NotificationPayload
from app.notifications.providers.base import EmailProvider, WebhookProvider
from app.notifications.providers.email_fake import FakeEmailProvider
from app.notifications.providers.email_smtp import SMTPProvider
from app.notifications.providers.webhook_fake import FakeWebhookProvider
from app.notifications.providers.webhook_http import HTTPWebhookProvider
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.notification import NotificationRepository
from app.repositories.notification_delivery import NotificationDeliveryRepository
from app.repositories.notification_preference import NotificationPreferenceRepository

logger = logging.getLogger(__name__)


class NotificationDeliveryWorker:
    """Processes pending and retryable notification deliveries using atomic claims and exponential backoff."""

    def __init__(
        self,
        db: Session,
        email_provider: Optional[EmailProvider] = None,
        webhook_provider: Optional[WebhookProvider] = None,
    ) -> None:
        self.db = db
        self.settings = get_settings()

        # Repositories
        self.delivery_repo = NotificationDeliveryRepository(db)
        self.notification_repo = NotificationRepository(db)
        self.preference_repo = NotificationPreferenceRepository(db)
        self.profile_repo = CandidateProfileRepository(db)

        # Providers
        if email_provider is not None:
            self.email_provider = email_provider
        elif self.settings.EMAIL_NOTIFICATIONS_ENABLED and self.settings.EMAIL_PROVIDER == "smtp":
            self.email_provider = SMTPProvider(
                host=self.settings.SMTP_HOST,
                port=self.settings.SMTP_PORT,
                username=self.settings.SMTP_USERNAME,
                password=self.settings.SMTP_PASSWORD,
                from_email=self.settings.SMTP_FROM_EMAIL,
                from_name=self.settings.SMTP_FROM_NAME,
                use_tls=self.settings.SMTP_USE_TLS,
                timeout=self.settings.SMTP_TIMEOUT_SECONDS,
            )
        else:
            self.email_provider = FakeEmailProvider()

        if webhook_provider is not None:
            self.webhook_provider = webhook_provider
        elif self.settings.WEBHOOK_NOTIFICATIONS_ENABLED:
            self.webhook_provider = HTTPWebhookProvider(timeout=self.settings.WEBHOOK_TIMEOUT_SECONDS)
        else:
            self.webhook_provider = FakeWebhookProvider()

        # Channels
        self.channels: Dict[str, NotificationChannel] = {
            NotificationChannelType.EMAIL.value: EmailChannel(self.email_provider),
            NotificationChannelType.WEBHOOK.value: WebhookChannel(self.webhook_provider),
        }

    def process_pending_deliveries(self, limit: int = 50) -> int:
        """Scan and dispatch pending or retryable deliveries.

        Recovers stale PROCESSING tasks first, claims deliveries atomically,
        and dispatches to their respective channel providers.

        Returns:
            Number of deliveries successfully dispatched in this run.
        """
        # 1. Recover stale tasks stuck in PROCESSING
        recovered = self.delivery_repo.recover_stale_processing(
            timeout_seconds=self.settings.NOTIFICATION_PROCESSING_TIMEOUT_SECONDS
        )
        if recovered > 0:
            logger.info("notification.worker.stale_recovered count=%d", recovered)

        # 2. Fetch pending or retryable deliveries
        pending_items = self.delivery_repo.get_pending_or_retryable(limit=limit)
        successful_count = 0

        for item in pending_items:
            # Atomic claim
            claimed = self.delivery_repo.claim_for_processing(item.id)
            if not claimed:
                continue

            success = self._dispatch_claimed_delivery(item.id)
            if success:
                successful_count += 1

        return successful_count

    def dispatch_single_delivery(self, delivery_id: UUID) -> bool:
        """Atomically claim and dispatch a specific delivery record."""
        claimed = self.delivery_repo.claim_for_processing(delivery_id)
        if not claimed:
            logger.warning("notification.worker.claim_failed delivery_id=%s", delivery_id)
            return False

        return self._dispatch_claimed_delivery(delivery_id)

    def _dispatch_claimed_delivery(self, delivery_id: UUID) -> bool:
        """Execute channel dispatch for a delivery that has already been transitioned to PROCESSING."""
        delivery = self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            return False

        notification = self.notification_repo.get_by_id(delivery.notification_id)
        if not notification:
            self.delivery_repo.record_failure(
                delivery_id=delivery.id,
                error="Parent notification record not found",
                is_transient=False,
            )
            return False

        profile = self.profile_repo.get_by_id(notification.profile_id)
        prefs = self.preference_repo.get_by_profile_id(notification.profile_id)

        # Validate channel exists
        if delivery.channel not in self.channels:
            self.delivery_repo.record_failure(
                delivery_id=delivery.id,
                error=f"Unsupported notification channel: {delivery.channel}",
                is_transient=False,
            )
            self._update_parent_notification_status(notification.id)
            return False

        channel = self.channels[delivery.channel]

        # Recipient extraction
        user = profile.user if profile else None
        recipient_email = user.email if user else None
        recipient_name = (
            f"{profile.first_name or ''} {profile.last_name or ''}".strip()
            if profile
            else None
        )

        # Pre-delivery validations
        if delivery.channel == NotificationChannelType.EMAIL.value:
            if not user or not recipient_email:
                self.delivery_repo.record_failure(
                    delivery_id=delivery.id,
                    error="Candidate account or email address is missing",
                    is_transient=False,
                )
                self._update_parent_notification_status(notification.id)
                return False

            if self.settings.EMAIL_REQUIRE_VERIFIED and not user.is_verified:
                self.delivery_repo.record_failure(
                    delivery_id=delivery.id,
                    error="Candidate email address is unverified",
                    is_transient=False,
                )
                self._update_parent_notification_status(notification.id)
                return False

        elif delivery.channel == NotificationChannelType.WEBHOOK.value:
            if not prefs or not prefs.webhook_url:
                self.delivery_repo.record_failure(
                    delivery_id=delivery.id,
                    error="Candidate has no webhook URL configured",
                    is_transient=False,
                )
                self._update_parent_notification_status(notification.id)
                return False

        # Build payload
        payload_data = notification.payload or {}
        payload = NotificationPayload(
            notification_id=notification.id,
            delivery_id=delivery.id,
            profile_id=notification.profile_id,
            event_type=notification.event_type,
            title=notification.title,
            body=notification.body,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            webhook_url=prefs.webhook_url if prefs else None,
            webhook_secret=prefs.webhook_secret if prefs else None,
            job_data=payload_data.get("job", {}),
            match_data=payload_data.get("match", {}),
        )

        # Dispatch via channel
        start_time = datetime.now(timezone.utc)
        logger.info(
            "notification.delivery.started delivery_id=%s notification_id=%s channel=%s attempt=%d",
            delivery.id,
            notification.id,
            delivery.channel,
            delivery.attempt_count + 1,
        )

        try:
            result: DeliveryResult = channel.send(payload)
        except Exception as exc:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            logger.exception(
                "notification.delivery.exception delivery_id=%s channel=%s duration_ms=%.1f",
                delivery.id,
                delivery.channel,
                duration_ms,
            )
            self.delivery_repo.record_failure(
                delivery_id=delivery.id,
                error=f"Unexpected error: {str(exc)}",
                is_transient=True,
            )
            self._update_parent_notification_status(notification.id)
            return False

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        if result.success:
            self.delivery_repo.record_success(
                delivery_id=delivery.id,
                provider_message_id=result.provider_message_id,
            )
            logger.info(
                "notification.delivery.sent delivery_id=%s notification_id=%s channel=%s duration_ms=%.1f msg_id=%s",
                delivery.id,
                notification.id,
                delivery.channel,
                duration_ms,
                result.provider_message_id,
            )
            self._update_parent_notification_status(notification.id)
            return True
        else:
            self.delivery_repo.record_failure(
                delivery_id=delivery.id,
                error=result.error_message or "Delivery failed",
                is_transient=result.is_transient,
                retry_delay_seconds=result.retry_after_seconds,
            )
            logger.warning(
                "notification.delivery.failed delivery_id=%s channel=%s transient=%s duration_ms=%.1f error=%s",
                delivery.id,
                delivery.channel,
                result.is_transient,
                duration_ms,
                result.error_message,
            )
            self._update_parent_notification_status(notification.id)
            return False

    def _update_parent_notification_status(self, notification_id: UUID) -> None:
        """Inspect deliveries for notification and synchronize parent Notification status."""
        stmt = select(NotificationDelivery).where(NotificationDelivery.notification_id == notification_id)
        deliveries = list(self.db.scalars(stmt).all())
        if not deliveries:
            return

        notification = self.notification_repo.get_by_id(notification_id)
        if not notification:
            return

        statuses = [d.status for d in deliveries]

        if any(s == DeliveryStatus.SENT.value for s in statuses):
            if notification.status != NotificationStatus.SENT.value:
                self.notification_repo.update_status(
                    notification_id=notification_id,
                    status=NotificationStatus.SENT.value,
                    sent_at=datetime.now(timezone.utc),
                )
        elif all(s == DeliveryStatus.FAILED.value for s in statuses):
            if notification.status != NotificationStatus.FAILED.value:
                self.notification_repo.update_status(
                    notification_id=notification_id,
                    status=NotificationStatus.FAILED.value,
                )
