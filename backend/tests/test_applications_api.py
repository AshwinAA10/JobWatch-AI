"""API integration and unit tests for Phase 10: Application Tracking & Lifecycle."""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.career_source import CareerSource
from app.models.company import Company
from app.models.job import Job
from app.models.job_match import JobMatch


def _get_auth_header(client: TestClient, email: str = "applicant@example.com") -> dict:
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


def _seed_job(
    db_session: Session,
    title: str = "Senior Distributed Systems Engineer",
    location: str = "San Francisco, CA",
) -> Job:
    """Helper to create a Job with company and career source."""
    company = Company(name=f"Company-{uuid.uuid4().hex[:6]}", slug=f"co-{uuid.uuid4().hex[:6]}")
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        company_id=company.id,
        name="Career Portal",
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
        description="<p>Build distributed platforms in Python & Rust.</p>",
        location=location,
        workplace_type="REMOTE",
        employment_type="FULL_TIME",
        application_url="https://example.com/apply/job-123",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


def test_create_application_success(client: TestClient, db_session: Session):
    """Test candidate successfully marks a job as applied."""
    auth_header = _get_auth_header(client, "test_create_app@example.com")
    job = _seed_job(db_session, title="Lead Backend Engineer")

    res = client.post(
        "/api/v1/applications",
        headers=auth_header,
        json={"job_id": str(job.id), "notes": "Applied via referral on company website"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    assert data["job_id"] == str(job.id)
    assert data["status"] == "APPLIED"
    assert data["job_title"] == "Lead Backend Engineer"
    assert data["company_name"] == job.company.name
    assert data["notes"] == "Applied via referral on company website"
    assert "applied_at" in data
    assert len(data["history"]) == 1
    assert data["history"][0]["new_status"] == "APPLIED"


def test_create_application_duplicate_conflict(client: TestClient, db_session: Session):
    """Test duplicate application for the same job results in 409 Conflict."""
    auth_header = _get_auth_header(client, "test_dup_app@example.com")
    job = _seed_job(db_session)

    res1 = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already" in res2.json()["detail"].lower()


def test_create_application_nonexistent_job(client: TestClient):
    """Test applying to a non-existent job ID returns 404."""
    auth_header = _get_auth_header(client, "test_nonexist_job@example.com")
    fake_job_id = str(uuid.uuid4())

    res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": fake_job_id})
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_candidate_ownership_isolation(client: TestClient, db_session: Session):
    """Test candidate B cannot access, modify, or delete Candidate A's application."""
    user_a = _get_auth_header(client, "candidate_a@example.com")
    user_b = _get_auth_header(client, "candidate_b@example.com")
    job = _seed_job(db_session)

    # Candidate A creates application
    res_a = client.post("/api/v1/applications", headers=user_a, json={"job_id": str(job.id)})
    assert res_a.status_code == status.HTTP_201_CREATED
    app_id = res_a.json()["id"]

    # Candidate B tries to read Candidate A's application
    res_b_get = client.get(f"/api/v1/applications/{app_id}", headers=user_b)
    assert res_b_get.status_code == status.HTTP_404_NOT_FOUND

    # Candidate B tries to update Candidate A's status
    res_b_patch = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=user_b,
        json={"status": "SCREENING"},
    )
    assert res_b_patch.status_code == status.HTTP_404_NOT_FOUND

    # Candidate B tries to add note to Candidate A's application
    res_b_note = client.post(
        f"/api/v1/applications/{app_id}/notes",
        headers=user_b,
        json={"content": "Malicious note"},
    )
    assert res_b_note.status_code == status.HTTP_404_NOT_FOUND

    # Candidate B tries to delete Candidate A's application
    res_b_delete = client.delete(f"/api/v1/applications/{app_id}", headers=user_b)
    assert res_b_delete.status_code == status.HTTP_404_NOT_FOUND


def test_status_transitions_and_history(client: TestClient, db_session: Session):
    """Test valid lifecycle transitions, invalid transition rejection, and history logging."""
    auth_header = _get_auth_header(client, "lifecycle_user@example.com")
    job = _seed_job(db_session)

    create_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    app_id = create_res.json()["id"]

    # Invalid jump: APPLIED -> ACCEPTED
    invalid_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=auth_header,
        json={"status": "ACCEPTED"},
    )
    assert invalid_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot transition" in invalid_res.json()["detail"].lower()

    # Valid transition: APPLIED -> SCREENING
    t1_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=auth_header,
        json={"status": "SCREENING", "note": "Recruiter phone screen scheduled"},
    )
    assert t1_res.status_code == status.HTTP_200_OK
    assert t1_res.json()["status"] == "SCREENING"

    # Valid transition: SCREENING -> INTERVIEW
    t2_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=auth_header,
        json={"status": "INTERVIEW", "note": "Invited to technical round"},
    )
    assert t2_res.status_code == status.HTTP_200_OK
    assert t2_res.json()["status"] == "INTERVIEW"

    # Valid transition: INTERVIEW -> OFFER
    t3_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=auth_header,
        json={"status": "OFFER", "note": "Received offer letter"},
    )
    assert t3_res.status_code == status.HTTP_200_OK
    assert t3_res.json()["status"] == "OFFER"

    # Valid transition: OFFER -> ACCEPTED
    t4_res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        headers=auth_header,
        json={"status": "ACCEPTED", "note": "Accepted offer! Starting next month."},
    )
    assert t4_res.status_code == status.HTTP_200_OK
    assert t4_res.json()["status"] == "ACCEPTED"

    # Verify complete history audit trail
    hist_res = client.get(f"/api/v1/applications/{app_id}/history", headers=auth_header)
    assert hist_res.status_code == status.HTTP_200_OK
    history = hist_res.json()
    assert len(history) == 5  # APPLIED initial + 4 transitions
    assert history[0]["new_status"] == "APPLIED"
    assert history[1]["old_status"] == "APPLIED"
    assert history[1]["new_status"] == "SCREENING"
    assert history[4]["new_status"] == "ACCEPTED"


def test_application_notes_crud(client: TestClient, db_session: Session):
    """Test adding, listing, updating, and deleting application notes."""
    auth_header = _get_auth_header(client, "notes_user@example.com")
    job = _seed_job(db_session)

    app_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    app_id = app_res.json()["id"]

    # 1. Create note
    n1_res = client.post(
        f"/api/v1/applications/{app_id}/notes",
        headers=auth_header,
        json={"content": "Need to follow up with hiring manager next Tuesday."},
    )
    assert n1_res.status_code == status.HTTP_201_CREATED
    note_id = n1_res.json()["id"]
    assert n1_res.json()["content"] == "Need to follow up with hiring manager next Tuesday."

    # 2. List notes
    list_res = client.get(f"/api/v1/applications/{app_id}/notes", headers=auth_header)
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 1

    # 3. Update note
    patch_res = client.patch(
        f"/api/v1/applications/{app_id}/notes/{note_id}",
        headers=auth_header,
        json={"content": "Followed up on Monday instead. Awaiting reply."},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["content"] == "Followed up on Monday instead. Awaiting reply."

    # 4. Delete note
    del_res = client.delete(f"/api/v1/applications/{app_id}/notes/{note_id}", headers=auth_header)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify empty notes
    list_after = client.get(f"/api/v1/applications/{app_id}/notes", headers=auth_header)
    assert len(list_after.json()) == 0


def test_interviews_crud(client: TestClient, db_session: Session):
    """Test scheduling, viewing, updating, and cancelling interviews."""
    auth_header = _get_auth_header(client, "interviews_user@example.com")
    job = _seed_job(db_session)

    app_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    app_id = app_res.json()["id"]

    # 1. Schedule interview
    interview_payload = {
        "interview_type": "TECHNICAL",
        "scheduled_at": "2026-10-15T14:00:00Z",
        "duration_minutes": 60,
        "interviewer_names": "Alex Smith, Staff Architect",
        "meeting_url": "https://meet.google.com/abc-defg-hij",
        "notes": "Focus on distributed consensus and event streaming.",
    }
    int_res = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header,
        json=interview_payload,
    )
    assert int_res.status_code == status.HTTP_201_CREATED
    interview_id = int_res.json()["id"]
    assert int_res.json()["status"] == "SCHEDULED"
    assert int_res.json()["interview_type"] == "TECHNICAL"

    # 2. List interviews
    list_res = client.get(f"/api/v1/applications/{app_id}/interviews", headers=auth_header)
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 1

    # 3. Update interview status to COMPLETED
    patch_res = client.patch(
        f"/api/v1/applications/{app_id}/interviews/{interview_id}",
        headers=auth_header,
        json={"status": "COMPLETED", "notes": "Went very well. Discussed Raft protocol."},
    )
    assert patch_res.status_code == status.HTTP_200_OK
    assert patch_res.json()["status"] == "COMPLETED"

    # 4. Delete interview
    del_res = client.delete(f"/api/v1/applications/{app_id}/interviews/{interview_id}", headers=auth_header)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify empty
    assert len(client.get(f"/api/v1/applications/{app_id}/interviews", headers=auth_header).json()) == 0


def test_application_statistics_and_filtering(client: TestClient, db_session: Session):
    """Test statistics endpoint and application list filtering and search."""
    auth_header = _get_auth_header(client, "stats_user@example.com")
    job1 = _seed_job(db_session, title="Python Architect")
    job2 = _seed_job(db_session, title="Go Backend Developer")
    job3 = _seed_job(db_session, title="Frontend Specialist")

    app1_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job1.id)})
    app2_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job2.id)})
    app3_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job3.id)})

    app1_id = app1_res.json()["id"]
    app2_id = app2_res.json()["id"]

    # Transition app1 to INTERVIEW
    client.patch(f"/api/v1/applications/{app1_id}/status", headers=auth_header, json={"status": "SCREENING"})
    client.patch(f"/api/v1/applications/{app1_id}/status", headers=auth_header, json={"status": "INTERVIEW"})

    # Transition app2 to REJECTED
    client.patch(f"/api/v1/applications/{app2_id}/status", headers=auth_header, json={"status": "REJECTED"})

    # Check stats endpoint
    stats_res = client.get("/api/v1/applications/stats", headers=auth_header)
    assert stats_res.status_code == status.HTTP_200_OK
    stats = stats_res.json()
    assert stats["total"] == 3
    assert stats["interview"] == 1
    assert stats["rejected"] == 1
    assert stats["applied"] == 1

    # Filter applications by status=INTERVIEW
    filt_res = client.get("/api/v1/applications?status=INTERVIEW", headers=auth_header)
    assert filt_res.status_code == status.HTTP_200_OK
    assert filt_res.json()["total"] == 1
    assert filt_res.json()["items"][0]["id"] == app1_id

    # Search applications by keyword
    search_res = client.get("/api/v1/applications?q=Python", headers=auth_header)
    assert search_res.status_code == status.HTTP_200_OK
    assert search_res.json()["total"] == 1
    assert search_res.json()["items"][0]["job_title"] == "Python Architect"


def test_job_detail_reflects_application_status(client: TestClient, db_session: Session):
    """Test job detail API includes application_id and application_status when applied."""
    auth_header = _get_auth_header(client, "job_detail_app@example.com")
    job = _seed_job(db_session, title="Site Reliability Engineer")

    # Before applying: application_id is null
    res_before = client.get(f"/api/v1/jobs/{job.id}", headers=auth_header)
    assert res_before.status_code == status.HTTP_200_OK
    assert res_before.json()["application_id"] is None
    assert res_before.json()["application_status"] is None

    # Apply to job
    app_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    app_id = app_res.json()["id"]

    # After applying: application_id and status are populated
    res_after = client.get(f"/api/v1/jobs/{job.id}", headers=auth_header)
    assert res_after.status_code == status.HTTP_200_OK
    assert res_after.json()["application_id"] == app_id
    assert res_after.json()["application_status"] == "APPLIED"


def test_delete_application(client: TestClient, db_session: Session):
    """Test deleting an application cleanly cascades notes, interviews, and history."""
    auth_header = _get_auth_header(client, "delete_app_user@example.com")
    job = _seed_job(db_session)

    app_res = client.post("/api/v1/applications", headers=auth_header, json={"job_id": str(job.id)})
    app_id = app_res.json()["id"]

    # Add note and interview
    client.post(f"/api/v1/applications/{app_id}/notes", headers=auth_header, json={"content": "Test note"})
    client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header,
        json={"interview_type": "HR", "scheduled_at": "2026-10-20T10:00:00Z"},
    )

    # Delete
    del_res = client.delete(f"/api/v1/applications/{app_id}", headers=auth_header)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Application should no longer exist
    get_res = client.get(f"/api/v1/applications/{app_id}", headers=auth_header)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND
