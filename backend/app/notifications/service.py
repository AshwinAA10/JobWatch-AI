"""NotificationService orchestrating match event evaluation, eligibility, and dispatch."""

import hashlib
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.job import Job
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.notification_preference import NotificationPreference
from app.notifications.channels.base import NotificationChannel
from app.notifications.channels.email import EmailChannel
from app.notifications.channels.webhook import WebhookChannel
from app.notifications.config import (
    HIGH_QUALITY_MATCH_THRESHOLD,
    NotificationChannelType,
    NotificationType,
)
from app.notifications.exceptions import RateLimitExceededError, SSRFSecurityError
from app.notifications.payload import DeliveryResult, NotificationPayload
from app.notifications.providers.base import EmailProvider, WebhookProvider
from app.notifications.providers.email_fake import FakeEmailProvider
from app.notifications.providers.email_smtp import SMTPProvider
from app.notifications.providers.webhook_fake import FakeWebhookProvider
from app.notifications.providers.webhook_http import HTTPWebhookProvider, validate_webhook_url_ssrf
from app.repositories.candidate_profile import CandidateProfileRepository
from app.repositories.job import JobRepository
from app.repositories.notification import NotificationRepository
from app.repositories.notification_delivery import NotificationDeliveryRepository
from app.repositories.notification_preference import NotificationPreferenceRepository
from app.schemas.notification import NotificationPreferenceUpdate

logger = logging.getLogger(__name__)


class NotificationService:
    """Master coordinator for candidate alerts, preference evaluation, and multi-channel dispatch."""

    def __init__(
        self,
        db: Session,
        email_provider: Optional[EmailProvider] = None,
        webhook_provider: Optional[WebhookProvider] = None,
    ) -> None:
        self.db = db
        settings = get_settings()

        # Repositories
        self.notification_repo = NotificationRepository(db)
        self.delivery_repo = NotificationDeliveryRepository(db)
        self.preference_repo = NotificationPreferenceRepository(db)
        self.profile_repo = CandidateProfileRepository(db)
        self.job_repo = JobRepository(db)

        # Providers
        if email_provider is not None:
            self.email_provider = email_provider
        elif settings.EMAIL_NOTIFICATIONS_ENABLED and settings.EMAIL_PROVIDER == "smtp":
            self.email_provider = SMTPProvider(
                host=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                from_email=settings.SMTP_FROM_EMAIL,
                from_name=settings.SMTP_FROM_NAME,
                use_tls=settings.SMTP_USE_TLS,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )
        else:
            self.email_provider = FakeEmailProvider()

        if webhook_provider is not None:
            self.webhook_provider = webhook_provider
        elif settings.WEBHOOK_NOTIFICATIONS_ENABLED:
            self.webhook_provider = HTTPWebhookProvider(timeout=settings.WEBHOOK_TIMEOUT_SECONDS)
        else:
            self.webhook_provider = FakeWebhookProvider()

        # Channel Registry
        self.channels: Dict[str, NotificationChannel] = {
            NotificationChannelType.EMAIL.value: EmailChannel(self.email_provider),
            NotificationChannelType.WEBHOOK.value: WebhookChannel(self.webhook_provider),
        }

    @staticmethod
    def compute_idempotency_key(
        profile_id: UUID,
        event_type: str,
        job_id: UUID,
        scoring_version: str,
    ) -> str:
        """Derive deterministic SHA-256 idempotency key to prevent duplicate alerts."""
        raw = f"{profile_id}:{event_type}:{job_id}:{scoring_version}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_preferences(self, profile_id: UUID) -> NotificationPreference:
        """Retrieve candidate notification preferences (or default if not set)."""
        return self.preference_repo.get_or_create_default(profile_id)

    def update_preferences(
        self,
        profile_id: UUID,
        update_data: NotificationPreferenceUpdate,
    ) -> NotificationPreference:
        """Update candidate notification preferences, validating webhook URLs and managing cancellations."""
        # SSRF validation on webhook URL if updated
        if update_data.webhook_url:
            validate_webhook_url_ssrf(update_data.webhook_url)

        updated = self.preference_repo.upsert(
            profile_id=profile_id,
            email_enabled=update_data.email_enabled,
            webhook_enabled=update_data.webhook_enabled,
            webhook_url=update_data.webhook_url,
            webhook_secret=update_data.webhook_secret,
            minimum_match_score=update_data.minimum_match_score,
            frequency=update_data.frequency,
            max_per_hour=update_data.max_per_hour,
        )

        # Respect immediate unsubscribe/disable: cancel pending deliveries for disabled channels
        if update_data.email_enabled is False:
            cancelled = self.delivery_repo.cancel_pending_for_channel(profile_id, NotificationChannelType.EMAIL.value)
            logger.info("notification.preferences.channel_disabled channel=EMAIL cancelled=%d", cancelled)

        if update_data.webhook_enabled is False:
            cancelled = self.delivery_repo.cancel_pending_for_channel(profile_id, NotificationChannelType.WEBHOOK.value)
            logger.info("notification.preferences.channel_disabled channel=WEBHOOK cancelled=%d", cancelled)

        return updated

    def evaluate_and_notify_match(
        self,
        profile_id: UUID,
        job: Job,
        match_result: Any,
        explanation: Optional[Any] = None,
        force_immediate_dispatch: bool = False,
    ) -> Optional[Notification]:
        """Evaluate candidate match event against preferences, create notification, and queue deliveries.

        Returns:
            Created or existing Notification record, or None if match does not meet threshold/criteria.
        """
        settings = get_settings()
        if not settings.NOTIFICATIONS_ENABLED:
            logger.info("notification.service.disabled_by_flag profile_id=%s", profile_id)
            return None

        # 1. Load preferences
        prefs = self.get_preferences(profile_id)

        # 2. Score threshold check
        score = float(getattr(match_result, "score", 0.0))
        if score < prefs.minimum_match_score:
            logger.debug(
                "notification.eligibility.below_threshold profile_id=%s job_id=%s score=%.1f min=%.1f",
                profile_id,
                job.id,
                score,
                prefs.minimum_match_score,
            )
            return None

        # 3. Determine notification type
        event_type = (
            NotificationType.HIGH_QUALITY_MATCH.value
            if score >= HIGH_QUALITY_MATCH_THRESHOLD
            else NotificationType.NEW_MATCH.value
        )

        # 4. Hourly Flood Protection / Rate Limiting
        recent_count = self.notification_repo.count_sent_in_last_hour(profile_id)
        if recent_count >= prefs.max_per_hour:
            logger.warning(
                "notification.rate_limited profile_id=%s sent_last_hour=%d max_per_hour=%d",
                profile_id,
                recent_count,
                prefs.max_per_hour,
            )
            return None

        # 5. Idempotency Check (canonical job identity aware)
        canonical_job_id = job.canonical_job_id or job.id
        scoring_version = getattr(match_result, "scoring_version", "v1")
        idempotency_key = self.compute_idempotency_key(
            profile_id=profile_id,
            event_type=event_type,
            job_id=canonical_job_id,
            scoring_version=scoring_version,
        )

        existing = self.notification_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            logger.info(
                "notification.idempotency.hit profile_id=%s job_id=%s notification_id=%s",
                profile_id,
                job.id,
                existing.id,
            )
            return existing

        # 6. Build event metadata payload
        company_name = job.company.name if job.company else "Company"
        job_data = {
            "id": str(job.id),
            "canonical_id": str(canonical_job_id),
            "title": job.title,
            "company_name": company_name,
            "location": job.location,
            "workplace_type": job.workplace_type,
            "employment_type": job.employment_type,
            "application_url": job.application_url or job.source_url or "",
        }

        expl_data = None
        if explanation:
            if hasattr(explanation, "model_dump"):
                expl_data = explanation.model_dump()
            elif isinstance(explanation, dict):
                expl_data = explanation

        match_data = {
            "score": score,
            "scoring_version": scoring_version,
            "confidence": getattr(match_result, "confidence", "MEDIUM"),
            "matched_criteria": getattr(match_result, "matched_criteria", []),
            "missing_criteria": getattr(match_result, "missing_criteria", []),
            "reasons": getattr(match_result, "reasons", []),
            "explanation": expl_data,
        }

        title = f"[{score:.0f}% Match] {job.title} at {company_name}"
        body = (
            f"New position matching your profile: {job.title} at {company_name} "
            f"({job.location or 'Remote'}). Score: {score:.0f}%."
        )

        # 7. Persist Notification record
        notification = self.notification_repo.create(
            profile_id=profile_id,
            event_type=event_type,
            job_id=job.id,
            title=title,
            body=body,
            idempotency_key=idempotency_key,
            match_id=getattr(match_result, "id", None),
            payload={"job": job_data, "match": match_data},
        )

        # 8. Create channel delivery attempts based on candidate preferences and system config
        deliveries_created: List[NotificationDelivery] = []

        if prefs.email_enabled:
            delivery = self.delivery_repo.create_delivery(
                notification_id=notification.id,
                channel=NotificationChannelType.EMAIL.value,
                max_attempts=settings.NOTIFICATION_MAX_RETRIES,
            )
            deliveries_created.append(delivery)

        if prefs.webhook_enabled and prefs.webhook_url:
            delivery = self.delivery_repo.create_delivery(
                notification_id=notification.id,
                channel=NotificationChannelType.WEBHOOK.value,
                max_attempts=settings.NOTIFICATION_MAX_RETRIES,
            )
            deliveries_created.append(delivery)

        logger.info(
            "notification.created id=%s profile_id=%s type=%s channels=%s",
            notification.id,
            profile_id,
            event_type,
            [d.channel for d in deliveries_created],
        )

        # 9. If immediate dispatch requested or configured
        if force_immediate_dispatch and deliveries_created:
            self._dispatch_deliveries_immediate(notification, deliveries_created)

        return notification

    def _dispatch_deliveries_immediate(
        self,
        notification: Notification,
        deliveries: List[NotificationDelivery],
    ) -> None:
        """Deliver queued attempts immediately for testing or synchronous flows."""
        from app.notifications.worker import NotificationDeliveryWorker

        worker = NotificationDeliveryWorker(
            db=self.db,
            email_provider=self.email_provider,
            webhook_provider=self.webhook_provider,
        )
        for delivery in deliveries:
            worker.dispatch_single_delivery(delivery.id)
