"""Repository for Notification entity persistence and queries."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery


class NotificationRepository:
    """Data access repository for Notification events."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        profile_id: UUID,
        event_type: str,
        job_id: UUID,
        title: str,
        body: str,
        idempotency_key: str,
        match_id: Optional[UUID] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Persist a new notification record."""
        notification = Notification(
            profile_id=profile_id,
            event_type=event_type,
            job_id=job_id,
            match_id=match_id,
            title=title,
            body=body,
            idempotency_key=idempotency_key,
            payload=payload or {},
            status="PENDING",
            is_read=False,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Fetch notification by ID with eager deliveries."""
        stmt = (
            select(Notification)
            .where(Notification.id == notification_id)
            .options(selectinload(Notification.deliveries))
        )
        return self.db.scalars(stmt).first()

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Notification]:
        """Fetch notification matching an idempotency key to prevent duplicates."""
        stmt = (
            select(Notification)
            .where(Notification.idempotency_key == idempotency_key)
            .options(selectinload(Notification.deliveries))
        )
        return self.db.scalars(stmt).first()

    def list_for_profile(
        self,
        profile_id: UUID,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Notification], int, int]:
        """List notifications for candidate with filtering and pagination.

        Returns (items, total_filtered_count, unread_count).
        """
        # Base query
        stmt = (
            select(Notification)
            .where(Notification.profile_id == profile_id)
            .options(selectinload(Notification.deliveries))
            .order_by(Notification.created_at.desc())
        )

        if status:
            stmt = stmt.where(Notification.status == status)
        if event_type:
            stmt = stmt.where(Notification.event_type == event_type)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))

        # Count total filtered
        count_stmt = select(func.count(Notification.id)).where(Notification.profile_id == profile_id)
        if status:
            count_stmt = count_stmt.where(Notification.status == status)
        if event_type:
            count_stmt = count_stmt.where(Notification.event_type == event_type)
        if unread_only:
            count_stmt = count_stmt.where(Notification.is_read.is_(False))

        total = self.db.scalar(count_stmt) or 0

        # Unread total across profile
        unread_stmt = select(func.count(Notification.id)).where(
            Notification.profile_id == profile_id,
            Notification.is_read.is_(False),
        )
        unread_count = self.db.scalar(unread_stmt) or 0

        # Paginated items
        items = list(self.db.scalars(stmt.offset(skip).limit(limit)).all())
        return items, total, unread_count

    def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Mark single notification as read."""
        notif = self.get_by_id(notification_id)
        if notif and not notif.is_read:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)
            notif.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(notif)
        return notif

    def mark_all_as_read(self, profile_id: UUID) -> int:
        """Mark all unread notifications for a candidate as read."""
        stmt = select(Notification).where(
            Notification.profile_id == profile_id,
            Notification.is_read.is_(False),
        )
        unreads = list(self.db.scalars(stmt).all())
        now = datetime.now(timezone.utc)
        for notif in unreads:
            notif.is_read = True
            notif.read_at = now
            notif.updated_at = now
        self.db.commit()
        return len(unreads)

    def count_sent_in_last_hour(self, profile_id: UUID) -> int:
        """Count notifications created/sent for a profile in the past 60 minutes for rate protection."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        stmt = select(func.count(Notification.id)).where(
            Notification.profile_id == profile_id,
            Notification.created_at >= one_hour_ago,
        )
        return self.db.scalar(stmt) or 0

    def update_status(
        self,
        notification_id: UUID,
        status: str,
        sent_at: Optional[datetime] = None,
    ) -> Optional[Notification]:
        """Update overall notification status and optional sent_at timestamp."""
        notif = self.get_by_id(notification_id)
        if notif:
            notif.status = status
            if sent_at is not None:
                notif.sent_at = sent_at
            notif.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(notif)
        return notif
