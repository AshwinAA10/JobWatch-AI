"""Repository for NotificationDelivery persistence, atomic claim, and retry tracking."""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.models.notification_delivery import NotificationDelivery

logger = logging.getLogger(__name__)


class NotificationDeliveryRepository:
    """Data access repository for individual notification delivery attempts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_delivery(
        self,
        notification_id: UUID,
        channel: str,
        max_attempts: int = 4,
    ) -> NotificationDelivery:
        """Create a new pending delivery record for a notification channel."""
        delivery = NotificationDelivery(
            notification_id=notification_id,
            channel=channel,
            status="PENDING",
            attempt_count=0,
            max_attempts=max_attempts,
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def get_by_id(self, delivery_id: UUID) -> Optional[NotificationDelivery]:
        """Fetch delivery record by ID."""
        stmt = select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
        return self.db.scalars(stmt).first()

    def get_pending_or_retryable(self, limit: int = 50) -> List[NotificationDelivery]:
        """Fetch pending deliveries or retrying deliveries whose next_retry_at is past."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(NotificationDelivery)
            .where(
                or_(
                    NotificationDelivery.status == "PENDING",
                    (NotificationDelivery.status == "RETRYING") & (NotificationDelivery.next_retry_at <= now),
                )
            )
            .order_by(NotificationDelivery.created_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def claim_for_processing(self, delivery_id: UUID) -> bool:
        """Atomically claim delivery for processing, transitioning state to PROCESSING.

        Returns True if claimed successfully, False if another worker claimed it first.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(NotificationDelivery)
            .where(
                NotificationDelivery.id == delivery_id,
                or_(
                    NotificationDelivery.status == "PENDING",
                    (NotificationDelivery.status == "RETRYING") & (NotificationDelivery.next_retry_at <= now),
                ),
            )
            .values(
                status="PROCESSING",
                updated_at=now,
            )
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return (result.rowcount or 0) > 0

    def recover_stale_processing(self, timeout_seconds: int = 600) -> int:
        """Reset deliveries stuck in PROCESSING longer than timeout back to RETRYING or FAILED."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        now = datetime.now(timezone.utc)

        # 1. Stale deliveries with remaining attempts -> RETRYING
        retry_stmt = (
            update(NotificationDelivery)
            .where(
                NotificationDelivery.status == "PROCESSING",
                NotificationDelivery.updated_at <= cutoff,
                NotificationDelivery.attempt_count < NotificationDelivery.max_attempts,
            )
            .values(
                status="RETRYING",
                next_retry_at=now + timedelta(seconds=60),
                last_error=f"Recovered from stale PROCESSING (exceeded {timeout_seconds}s)",
                updated_at=now,
            )
        )
        retry_res = self.db.execute(retry_stmt)

        # 2. Stale deliveries with no attempts remaining -> FAILED
        fail_stmt = (
            update(NotificationDelivery)
            .where(
                NotificationDelivery.status == "PROCESSING",
                NotificationDelivery.updated_at <= cutoff,
                NotificationDelivery.attempt_count >= NotificationDelivery.max_attempts,
            )
            .values(
                status="FAILED",
                last_error=f"Permanently failed after stale PROCESSING timeout ({timeout_seconds}s)",
                updated_at=now,
            )
        )
        fail_res = self.db.execute(fail_stmt)
        self.db.commit()

        recovered_count = (retry_res.rowcount or 0) + (fail_res.rowcount or 0)
        if recovered_count > 0:
            logger.warning(
                "notification.worker.stale_recovery recovered=%d (retrying=%d, failed=%d)",
                recovered_count,
                retry_res.rowcount or 0,
                fail_res.rowcount or 0,
            )
        return recovered_count

    def record_success(
        self,
        delivery_id: UUID,
        provider_message_id: Optional[str] = None,
    ) -> Optional[NotificationDelivery]:
        """Record successful delivery dispatch."""
        delivery = self.get_by_id(delivery_id)
        if delivery:
            delivery.status = "SENT"
            delivery.attempt_count += 1
            delivery.provider_message_id = provider_message_id
            delivery.sent_at = datetime.now(timezone.utc)
            delivery.last_error = None
            delivery.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(delivery)
        return delivery

    def record_failure(
        self,
        delivery_id: UUID,
        error: str,
        is_transient: bool,
        retry_delay_seconds: Optional[float] = None,
    ) -> Optional[NotificationDelivery]:
        """Record delivery attempt failure, determining retry or permanent failure."""
        delivery = self.get_by_id(delivery_id)
        if not delivery:
            return None

        delivery.attempt_count += 1
        delivery.last_error = error
        now = datetime.now(timezone.utc)

        if is_transient and delivery.attempt_count < delivery.max_attempts:
            delay = retry_delay_seconds if retry_delay_seconds is not None else (60.0 * (2 ** (delivery.attempt_count - 1)))
            # Cap maximum delay to 1 hour
            delay = min(delay, 3600.0)
            delivery.status = "RETRYING"
            delivery.next_retry_at = now + timedelta(seconds=delay)
        else:
            delivery.status = "FAILED"
            delivery.next_retry_at = None

        delivery.updated_at = now
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def cancel_pending_for_channel(self, profile_id: UUID, channel: str) -> int:
        """Cancel pending and retrying deliveries for a candidate when channel is disabled."""
        from app.models.notification import Notification

        subquery = select(Notification.id).where(Notification.profile_id == profile_id)
        stmt = (
            update(NotificationDelivery)
            .where(
                NotificationDelivery.notification_id.in_(subquery),
                NotificationDelivery.channel == channel,
                NotificationDelivery.status.in_(["PENDING", "RETRYING"]),
            )
            .values(
                status="CANCELLED",
                last_error=f"Cancelled because {channel} was disabled in preferences",
                updated_at=datetime.now(timezone.utc),
            )
        )
        res = self.db.execute(stmt)
        self.db.commit()
        return res.rowcount or 0
