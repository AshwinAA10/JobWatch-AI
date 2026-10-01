"""Tests for background delivery worker, atomic claim, retries, and stale recovery."""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.candidate_profile import CandidateProfile
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.user import User
from app.notifications.config import DeliveryStatus, NotificationChannelType, NotificationStatus
from app.notifications.providers.email_fake import FakeEmailProvider
from app.notifications.providers.webhook_fake import FakeWebhookProvider
from app.notifications.worker import NotificationDeliveryWorker
from app.repositories.notification import NotificationRepository
from app.repositories.notification_delivery import NotificationDeliveryRepository


def _setup_notification_with_delivery(
    db_session: Session,
    channel: str = "EMAIL",
    is_verified: bool = True,
    email: str = "worker_user@example.com",
) -> tuple[Notification, NotificationDelivery]:
    """Helper to set up user, profile, job, notification, and delivery."""
    user = User(email=email, password_hash="hash", is_verified=is_verified)
    db_session.add(user)
    db_session.commit()

    profile = CandidateProfile(user_id=user.id, first_name="Alex", last_name="Rivera")
    db_session.add(profile)
    db_session.commit()

    company = Company(name="TechCorp", slug=f"techcorp-{uuid.uuid4().hex[:6]}")
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
        title="Senior Site Reliability Engineer",
        location="Remote",
        source_url="https://techcorp.com/jobs/1",
        application_url="https://techcorp.com/apply/1",
    )
    db_session.add(job)
    db_session.commit()

    notif_repo = NotificationRepository(db_session)
    notification = notif_repo.create(
        profile_id=profile.id,
        event_type="NEW_MATCH",
        job_id=job.id,
        title="New Match: Senior SRE",
        body="90% match for Senior SRE",
        idempotency_key=f"worker_test_{uuid.uuid4().hex}",
        payload={
            "job": {
                "title": job.title,
                "company_name": company.name,
                "location": job.location,
                "application_url": job.application_url,
            },
            "match": {
                "score": 90.0,
                "reasons": ["Linux kernel", "Distributed tracing"],
            },
        },
    )

    deliv_repo = NotificationDeliveryRepository(db_session)
    delivery = deliv_repo.create_delivery(
        notification_id=notification.id,
        channel=channel,
        max_attempts=3,
    )

    return notification, delivery


def test_worker_dispatches_pending_delivery_successfully(db_session: Session):
    """Verify worker picks up PENDING delivery, transitions it to SENT, and updates parent status."""
    email_provider = FakeEmailProvider()
    notif, delivery = _setup_notification_with_delivery(db_session, "EMAIL")

    worker = NotificationDeliveryWorker(
        db=db_session,
        email_provider=email_provider,
    )

    processed = worker.process_pending_deliveries()
    assert processed == 1

    db_session.refresh(delivery)
    assert delivery.status == DeliveryStatus.SENT.value
    assert delivery.attempt_count == 1
    assert delivery.provider_message_id is not None
    assert delivery.sent_at is not None

    db_session.refresh(notif)
    assert notif.status == NotificationStatus.SENT.value


def test_worker_handles_transient_failure_and_retries(db_session: Session):
    """Verify transient provider errors transition delivery to RETRYING with exponential backoff."""
    email_provider = FakeEmailProvider(should_fail=True, failure_type="transient")
    notif, delivery = _setup_notification_with_delivery(db_session, "EMAIL")

    worker = NotificationDeliveryWorker(
        db=db_session,
        email_provider=email_provider,
    )

    processed = worker.process_pending_deliveries()
    assert processed == 0

    db_session.refresh(delivery)
    assert delivery.status == DeliveryStatus.RETRYING.value
    assert delivery.attempt_count == 1
    assert delivery.next_retry_at is not None
    # Next retry should be in the future (handle SQLite offset-naive datetime)
    retry_time = delivery.next_retry_at.replace(tzinfo=timezone.utc) if delivery.next_retry_at.tzinfo is None else delivery.next_retry_at
    assert retry_time > datetime.now(timezone.utc)


def test_worker_exhausts_retries_to_failed(db_session: Session):
    """Verify that when max_attempts is reached, delivery transitions to FAILED."""
    email_provider = FakeEmailProvider(should_fail=True, failure_type="transient")
    notif, delivery = _setup_notification_with_delivery(db_session, "EMAIL")

    # Set attempt_count to max_attempts - 1
    delivery.attempt_count = 2
    delivery.max_attempts = 3
    db_session.commit()

    worker = NotificationDeliveryWorker(
        db=db_session,
        email_provider=email_provider,
    )

    processed = worker.process_pending_deliveries()
    assert processed == 0

    db_session.refresh(delivery)
    assert delivery.status == DeliveryStatus.FAILED.value
    assert delivery.attempt_count == 3
    assert delivery.next_retry_at is None

    db_session.refresh(notif)
    assert notif.status == NotificationStatus.FAILED.value


def test_stale_processing_recovery(db_session: Session):
    """Verify deliveries stuck in PROCESSING beyond timeout are recovered to RETRYING."""
    notif, delivery = _setup_notification_with_delivery(db_session, "EMAIL")

    # Simulate stale crash in PROCESSING 15 minutes ago
    deliv_repo = NotificationDeliveryRepository(db_session)
    claimed = deliv_repo.claim_for_processing(delivery.id)
    assert claimed is True

    past_time = datetime.now(timezone.utc) - timedelta(seconds=700)
    delivery.updated_at = past_time
    db_session.commit()

    recovered = deliv_repo.recover_stale_processing(timeout_seconds=600)
    assert recovered == 1

    db_session.refresh(delivery)
    assert delivery.status == DeliveryStatus.RETRYING.value
    assert "Recovered from stale PROCESSING" in delivery.last_error


def test_atomic_claim_concurrency(db_session: Session):
    """Verify that two workers cannot claim the same delivery simultaneously."""
    notif, delivery = _setup_notification_with_delivery(db_session, "EMAIL")
    deliv_repo = NotificationDeliveryRepository(db_session)

    # First claim succeeds
    claim1 = deliv_repo.claim_for_processing(delivery.id)
    assert claim1 is True

    # Second claim fails
    claim2 = deliv_repo.claim_for_processing(delivery.id)
    assert claim2 is False


def test_unverified_email_fails_when_verification_required(db_session: Session, monkeypatch):
    """Verify unverified emails are rejected with a permanent error when EMAIL_REQUIRE_VERIFIED=True."""
    settings = get_settings()
    monkeypatch.setattr(settings, "EMAIL_REQUIRE_VERIFIED", True)

    notif, delivery = _setup_notification_with_delivery(
        db_session,
        channel="EMAIL",
        is_verified=False,
        email="unverified@example.com",
    )

    worker = NotificationDeliveryWorker(
        db=db_session,
        email_provider=FakeEmailProvider(),
    )

    processed = worker.process_pending_deliveries()
    assert processed == 0

    db_session.refresh(delivery)
    assert delivery.status == DeliveryStatus.FAILED.value
    assert "unverified" in delivery.last_error.lower()
