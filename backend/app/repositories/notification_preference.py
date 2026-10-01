"""Repository for candidate notification preferences persistence."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference


class NotificationPreferenceRepository:
    """Data access repository for NotificationPreference records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_profile_id(self, profile_id: UUID) -> Optional[NotificationPreference]:
        """Fetch notification preferences for a candidate profile."""
        stmt = select(NotificationPreference).where(NotificationPreference.profile_id == profile_id)
        return self.db.scalars(stmt).first()

    def get_or_create_default(self, profile_id: UUID) -> NotificationPreference:
        """Fetch existing preferences or instantiate safe defaults."""
        existing = self.get_by_profile_id(profile_id)
        if existing:
            return existing

        default_prefs = NotificationPreference(
            profile_id=profile_id,
            email_enabled=False,
            webhook_enabled=False,
            minimum_match_score=75.0,
            frequency="IMMEDIATE",
            max_per_hour=10,
        )
        self.db.add(default_prefs)
        self.db.commit()
        self.db.refresh(default_prefs)
        return default_prefs

    def upsert(
        self,
        profile_id: UUID,
        email_enabled: Optional[bool] = None,
        webhook_enabled: Optional[bool] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        minimum_match_score: Optional[float] = None,
        frequency: Optional[str] = None,
        max_per_hour: Optional[int] = None,
    ) -> NotificationPreference:
        """Create or update candidate notification preferences."""
        prefs = self.get_or_create_default(profile_id)

        if email_enabled is not None:
            prefs.email_enabled = email_enabled
        if webhook_enabled is not None:
            prefs.webhook_enabled = webhook_enabled
        if webhook_url is not None:
            prefs.webhook_url = webhook_url
        if webhook_secret is not None:
            prefs.webhook_secret = webhook_secret
        if minimum_match_score is not None:
            prefs.minimum_match_score = minimum_match_score
        if frequency is not None:
            prefs.frequency = frequency
        if max_per_hour is not None:
            prefs.max_per_hour = max_per_hour

        prefs.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(prefs)
        return prefs
