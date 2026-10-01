"""Tests for notification eligibility, scoring thresholds, idempotency, and flood control."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.candidate_profile import CandidateProfile
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.user import User
from app.notifications.config import (
    HIGH_QUALITY_MATCH_THRESHOLD,
    NotificationChannelType,
    NotificationType,
)
from app.notifications.providers.email_fake import FakeEmailProvider
from app.notifications.providers.webhook_fake import FakeWebhookProvider
from app.notifications.service import NotificationService
from app.schemas.notification import NotificationPreferenceUpdate


@dataclass
class MockMatchResult:
    score: float
    scoring_version: str = "hybrid-v1"
    confidence: str = "HIGH"
    matched_criteria: List[str] = field(default_factory=lambda: ["Python", "FastAPI"])
    missing_criteria: List[str] = field(default_factory=lambda: ["Kubernetes"])
    reasons: List[str] = field(default_factory=lambda: ["Strong backend framework overlap"])
    id: Optional[uuid.UUID] = None


def _create_candidate(db_session: Session, email: str = "candidate@example.com") -> CandidateProfile:
    user = User(email=email, password_hash="hash", is_verified=True)
    db_session.add(user)
    db_session.commit()
    profile = CandidateProfile(
        user_id=user.id,
        first_name="Jane",
        last_name="Doe",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def _create_job(db_session: Session, title: str = "Staff Backend Engineer") -> Job:
    company = Company(name="Acme Corp", slug=f"acme-{uuid.uuid4().hex[:6]}")
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        company_id=company.id,
        name="Main Careers",
        source_type="greenhouse",
        base_url=f"https://boards.greenhouse.io/{company.slug}",
    )
    db_session.add(source)
    db_session.commit()

    job = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"ext-{uuid.uuid4().hex[:8]}",
        title=title,
        location="San Francisco, CA",
        workplace_type="HYBRID",
        employment_type="FULL_TIME",
        source_url="https://acme.com/jobs/1",
        application_url="https://acme.com/apply/1",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_eligible_match_creates_notification(db_session: Session):
    """Verify that match score exceeding threshold creates Notification and deliveries."""
    profile = _create_candidate(db_session, "eligible@example.com")
    job = _create_job(db_session)

    service = NotificationService(
        db=db_session,
        email_provider=FakeEmailProvider(),
        webhook_provider=FakeWebhookProvider(),
    )

    # Enable email in preferences
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=True, minimum_match_score=75.0),
    )

    match = MockMatchResult(score=80.0)
    notification = service.evaluate_and_notify_match(
        profile_id=profile.id,
        job=job,
        match_result=match,
    )

    assert notification is not None
    assert notification.event_type == NotificationType.NEW_MATCH.value
    assert notification.profile_id == profile.id
    assert notification.job_id == job.id
    assert notification.status == "PENDING"
    assert len(notification.deliveries) == 1
    assert notification.deliveries[0].channel == NotificationChannelType.EMAIL.value


def test_below_threshold_creates_no_notification(db_session: Session):
    """Verify that match score below candidate preference threshold creates no alert."""
    profile = _create_candidate(db_session, "below_threshold@example.com")
    job = _create_job(db_session)

    service = NotificationService(db=db_session)
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=True, minimum_match_score=80.0),
    )

    match = MockMatchResult(score=72.0)
    notification = service.evaluate_and_notify_match(
        profile_id=profile.id,
        job=job,
        match_result=match,
    )

    assert notification is None


def test_high_quality_match_event_type(db_session: Session):
    """Verify that match score >= 85% is assigned HIGH_QUALITY_MATCH event type."""
    profile = _create_candidate(db_session, "hq_match@example.com")
    job = _create_job(db_session)

    service = NotificationService(db=db_session)
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=True, minimum_match_score=70.0),
    )

    match = MockMatchResult(score=88.0)
    notification = service.evaluate_and_notify_match(
        profile_id=profile.id,
        job=job,
        match_result=match,
    )

    assert notification is not None
    assert notification.event_type == NotificationType.HIGH_QUALITY_MATCH.value


def test_idempotency_duplicate_prevention(db_session: Session):
    """Verify that evaluating the exact same match twice yields the identical Notification record."""
    profile = _create_candidate(db_session, "idempotent@example.com")
    job = _create_job(db_session)

    service = NotificationService(db=db_session)
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=True, minimum_match_score=70.0),
    )

    match = MockMatchResult(score=79.0, scoring_version="hybrid-v1")
    first_notif = service.evaluate_and_notify_match(profile.id, job, match)
    second_notif = service.evaluate_and_notify_match(profile.id, job, match)

    assert first_notif is not None
    assert second_notif is not None
    assert first_notif.id == second_notif.id


def test_canonical_job_duplicate_prevention(db_session: Session):
    """Verify that multiple postings sharing a canonical_job_id do not trigger duplicate notifications."""
    profile = _create_candidate(db_session, "canonical_dedup@example.com")

    # Canonical job
    canonical_job = _create_job(db_session, "Senior Python Developer - Canonical")

    # Duplicate job pointing to canonical
    dup_job = _create_job(db_session, "Senior Python Developer - Duplicate")
    dup_job.canonical_job_id = canonical_job.id
    db_session.commit()

    service = NotificationService(db=db_session)
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=True, minimum_match_score=70.0),
    )

    match = MockMatchResult(score=85.0)
    notif1 = service.evaluate_and_notify_match(profile.id, canonical_job, match)
    notif2 = service.evaluate_and_notify_match(profile.id, dup_job, match)

    assert notif1 is not None
    assert notif2 is not None
    # Both point to the same notification because the idempotency key binds to canonical_job_id
    assert notif1.id == notif2.id


def test_hourly_rate_limiting_flood_control(db_session: Session):
    """Verify candidate hourly notification flood control."""
    profile = _create_candidate(db_session, "rate_limited@example.com")
    service = NotificationService(db=db_session)

    # Set hourly cap to 2
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(
            email_enabled=True,
            minimum_match_score=70.0,
            max_per_hour=2,
        ),
    )

    match = MockMatchResult(score=85.0)

    # Send 1st
    job1 = _create_job(db_session, "Job 1")
    n1 = service.evaluate_and_notify_match(profile.id, job1, match)
    assert n1 is not None

    # Send 2nd
    job2 = _create_job(db_session, "Job 2")
    n2 = service.evaluate_and_notify_match(profile.id, job2, match)
    assert n2 is not None

    # 3rd should be rate limited and return None
    job3 = _create_job(db_session, "Job 3")
    n3 = service.evaluate_and_notify_match(profile.id, job3, match)
    assert n3 is None


def test_disabling_channel_cancels_pending_deliveries(db_session: Session):
    """Verify that disabling a notification channel cancels queued deliveries immediately."""
    profile = _create_candidate(db_session, "cancel_channel@example.com")
    job = _create_job(db_session)

    service = NotificationService(db=db_session)
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=True, minimum_match_score=70.0),
    )

    notif = service.evaluate_and_notify_match(profile.id, job, MockMatchResult(score=80.0))
    assert notif is not None
    assert notif.deliveries[0].status == "PENDING"

    # Now disable email
    service.update_preferences(
        profile.id,
        NotificationPreferenceUpdate(email_enabled=False),
    )

    # Delivery should now be CANCELLED
    db_session.refresh(notif.deliveries[0])
    assert notif.deliveries[0].status == "CANCELLED"
