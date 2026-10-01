"""API tests for notification history, mark as read, candidate isolation, and delivery trigger."""

import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.candidate_profile import CandidateProfile
from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.repositories.notification_delivery import NotificationDeliveryRepository


def _get_auth_header(client: TestClient, email: str) -> dict:
    """Helper to register and login a user, returning Authorization header."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_notification(db_session: Session, user_email: str, title: str = "Test Job Match"):
    """Helper to seed a notification for a user."""
    user = db_session.query(User).filter(User.email == user_email).first()
    profile = db_session.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()

    company = Company(name="SeedCorp", slug=f"seedcorp-{uuid.uuid4().hex[:6]}")
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        company_id=company.id,
        name="Seed Source",
        source_type="lever",
        base_url=f"https://jobs.lever.co/{company.slug}",
    )
    db_session.add(source)
    db_session.commit()

    job = Job(
        company_id=company.id,
        career_source_id=source.id,
        external_id=f"ext-{uuid.uuid4().hex[:8]}",
        title="Software Engineer",
        source_url="https://seed.com/job/1",
    )
    db_session.add(job)
    db_session.commit()

    repo = NotificationRepository(db_session)
    notif = repo.create(
        profile_id=profile.id,
        event_type="NEW_MATCH",
        job_id=job.id,
        title=title,
        body="Detailed body",
        idempotency_key=f"seed_{uuid.uuid4().hex}",
        payload={"job": {"title": job.title}},
    )

    deliv_repo = NotificationDeliveryRepository(db_session)
    deliv_repo.create_delivery(notif.id, channel="EMAIL")

    return notif


def test_list_notifications_and_filtering(client: TestClient, db_session: Session):
    """Verify paginated listing and filtering by unread/status."""
    email = "list_notifs@example.com"
    headers = _get_auth_header(client, email)

    # Initialize profile
    client.get("/api/v1/profile", headers=headers)

    # Seed 3 notifications
    n1 = _seed_notification(db_session, email, "Job 1")
    n2 = _seed_notification(db_session, email, "Job 2")
    n3 = _seed_notification(db_session, email, "Job 3")

    # Mark 1 as read
    repo = NotificationRepository(db_session)
    repo.mark_as_read(n1.id)

    # List all
    res = client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total"] == 3
    assert data["unread_count"] == 2
    assert len(data["items"]) == 3

    # Filter unread only
    unread_res = client.get("/api/v1/notifications?unread_only=true", headers=headers)
    assert unread_res.status_code == status.HTTP_200_OK
    unread_data = unread_res.json()
    assert unread_data["total"] == 2
    assert len(unread_data["items"]) == 2


def test_candidate_isolation_forbidden_access(client: TestClient, db_session: Session):
    """Verify Candidate A cannot access or mark Candidate B's notification as read."""
    headers_a = _get_auth_header(client, "user_a@example.com")
    headers_b = _get_auth_header(client, "user_b@example.com")

    client.get("/api/v1/profile", headers=headers_a)
    client.get("/api/v1/profile", headers=headers_b)

    notif_a = _seed_notification(db_session, "user_a@example.com", "Private Job for A")

    # Candidate B tries to read Candidate A's notification
    get_res = client.get(f"/api/v1/notifications/{notif_a.id}", headers=headers_b)
    assert get_res.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized" in get_res.json()["detail"].lower()

    # Candidate B tries to mark Candidate A's notification as read
    post_res = client.post(f"/api/v1/notifications/{notif_a.id}/read", headers=headers_b)
    assert post_res.status_code == status.HTTP_403_FORBIDDEN


def test_mark_as_read_lifecycle(client: TestClient, db_session: Session):
    """Verify marking single and all notifications as read."""
    email = "read_lifecycle@example.com"
    headers = _get_auth_header(client, email)
    client.get("/api/v1/profile", headers=headers)

    n1 = _seed_notification(db_session, email, "Notice 1")
    n2 = _seed_notification(db_session, email, "Notice 2")

    # Mark single as read
    res1 = client.post(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["is_read"] is True
    assert res1.json()["read_at"] is not None

    # Check unread count is now 1
    list_res = client.get("/api/v1/notifications", headers=headers)
    assert list_res.json()["unread_count"] == 1

    # Mark all as read
    all_res = client.post("/api/v1/notifications/read-all", headers=headers)
    assert all_res.status_code == status.HTTP_200_OK
    assert all_res.json()["marked_read"] == 1

    # Check unread count is now 0
    final_res = client.get("/api/v1/notifications", headers=headers)
    assert final_res.json()["unread_count"] == 0


def test_deliveries_process_trigger(client: TestClient, db_session: Session):
    """Verify endpoint to trigger delivery processing executes worker."""
    email = "process_trigger@example.com"
    headers = _get_auth_header(client, email)
    client.get("/api/v1/profile", headers=headers)

    _seed_notification(db_session, email, "To be delivered")

    res = client.post("/api/v1/notifications/deliveries/process?limit=10", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "ok"
    assert data["delivered_count"] >= 1
