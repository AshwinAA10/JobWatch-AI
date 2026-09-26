"""API integration tests for candidate profile, skills, experience, education, and preferences."""

from fastapi import status
from fastapi.testclient import TestClient


def _get_auth_header(client: TestClient, email: str = "candidate@example.com") -> dict:
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


def test_profile_lifecycle(client: TestClient):
    """Verify getting, initializing, and updating candidate profile."""
    headers = _get_auth_header(client, "profile_user@example.com")

    # 1. Get profile (automatically creates empty profile if not existing)
    res = client.get("/api/v1/profile", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["profile_completion_percent"] == 0
    assert data["skills"] == []

    # 2. Update profile
    update_payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "headline": "Lead Distributed Systems Engineer",
        "city": "Seattle",
        "state": "WA",
        "country": "USA",
        "years_of_experience": 8.5,
        "bio": "Building scalable cloud architectures.",
    }
    update_res = client.put("/api/v1/profile", json=update_payload, headers=headers)
    assert update_res.status_code == status.HTTP_200_OK
    updated_data = update_res.json()
    assert updated_data["first_name"] == "Alice"
    assert updated_data["years_of_experience"] == 8.5
    # Completeness should have increased (basic identity + headline + bio = 35%)
    assert updated_data["profile_completion_percent"] >= 35


def test_skills_management(client: TestClient):
    """Verify attaching, updating, and removing skills."""
    headers = _get_auth_header(client, "skills_user@example.com")

    # 1. Attach skill
    skill_payload = {
        "skill_name": "Python",
        "proficiency": "EXPERT",
        "years_experience": 5.0,
    }
    add_res = client.post("/api/v1/profile/skills", json=skill_payload, headers=headers)
    assert add_res.status_code == status.HTTP_201_CREATED
    skill_data = add_res.json()
    assert skill_data["skill"]["name"] == "Python"
    assert skill_data["proficiency"] == "EXPERT"
    skill_assoc_id = skill_data["id"]

    # 2. Duplicate attachment should return 409
    dup_res = client.post("/api/v1/profile/skills", json=skill_payload, headers=headers)
    assert dup_res.status_code == status.HTTP_409_CONFLICT

    # 3. List skills
    list_res = client.get("/api/v1/profile/skills", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.json()) == 1

    # 4. Update skill
    upd_res = client.put(
        f"/api/v1/profile/skills/{skill_assoc_id}",
        json={"proficiency": "ADVANCED", "years_experience": 6.0},
        headers=headers,
    )
    assert upd_res.status_code == status.HTTP_200_OK
    assert upd_res.json()["proficiency"] == "ADVANCED"
    assert upd_res.json()["years_experience"] == 6.0

    # 5. Remove skill
    del_res = client.delete(f"/api/v1/profile/skills/{skill_assoc_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify list is empty
    list_res2 = client.get("/api/v1/profile/skills", headers=headers)
    assert len(list_res2.json()) == 0


def test_experience_management(client: TestClient):
    """Verify adding, updating, and deleting work experience entries."""
    headers = _get_auth_header(client, "exp_user@example.com")

    # 1. Add experience
    payload = {
        "company_name": "Stripe",
        "job_title": "Software Engineer",
        "description": "Payments infrastructure",
        "location": "San Francisco, CA",
        "start_date": "2021-06-01",
        "is_current": True,
    }
    res = client.post("/api/v1/profile/experience", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    exp_id = res.json()["id"]
    assert res.json()["company_name"] == "Stripe"
    assert res.json()["is_current"] is True

    # 2. Update experience
    upd_res = client.put(
        f"/api/v1/profile/experience/{exp_id}",
        json={"job_title": "Senior Software Engineer"},
        headers=headers,
    )
    assert upd_res.status_code == status.HTTP_200_OK
    assert upd_res.json()["job_title"] == "Senior Software Engineer"

    # 3. Delete experience
    del_res = client.delete(f"/api/v1/profile/experience/{exp_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify empty
    list_res = client.get("/api/v1/profile/experience", headers=headers)
    assert len(list_res.json()) == 0


def test_education_management(client: TestClient):
    """Verify adding, updating, and deleting education records."""
    headers = _get_auth_header(client, "edu_user@example.com")

    # 1. Add education
    payload = {
        "institution_name": "MIT",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "start_date": "2016-09-01",
        "end_date": "2020-05-30",
    }
    res = client.post("/api/v1/profile/education", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    edu_id = res.json()["id"]

    # 2. Update education
    upd_res = client.put(
        f"/api/v1/profile/education/{edu_id}",
        json={"grade": "3.9 GPA"},
        headers=headers,
    )
    assert upd_res.status_code == status.HTTP_200_OK
    assert upd_res.json()["grade"] == "3.9 GPA"

    # 3. Delete education
    del_res = client.delete(f"/api/v1/profile/education/{edu_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT


def test_preferences_management(client: TestClient):
    """Verify getting and updating job search preferences."""
    headers = _get_auth_header(client, "prefs_user@example.com")

    prefs_payload = {
        "desired_titles": ["Senior Backend Engineer", "Distributed Systems Engineer"],
        "preferred_locations": ["Remote", "San Francisco, CA"],
        "workplace_types": ["REMOTE", "HYBRID"],
        "employment_types": ["FULL_TIME"],
        "minimum_salary": 160000,
        "maximum_salary": 220000,
        "salary_currency": "USD",
        "willing_to_relocate": True,
    }
    res = client.put("/api/v1/profile/preferences", json=prefs_payload, headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "Senior Backend Engineer" in data["desired_titles"]
    assert data["minimum_salary"] == 160000
    assert data["willing_to_relocate"] is True

    # Get preferences
    get_res = client.get("/api/v1/profile/preferences", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["maximum_salary"] == 220000


def test_cross_user_isolation(client: TestClient):
    """Verify that User B cannot modify or delete User A's resources."""
    headers_a = _get_auth_header(client, "user_a@example.com")
    headers_b = _get_auth_header(client, "user_b@example.com")

    # User A creates a skill and experience
    skill_res = client.post(
        "/api/v1/profile/skills",
        json={"skill_name": "Rust", "proficiency": "ADVANCED"},
        headers=headers_a,
    )
    skill_assoc_id = skill_res.json()["id"]

    exp_res = client.post(
        "/api/v1/profile/experience",
        json={
            "company_name": "Tech Corp",
            "job_title": "Developer",
            "start_date": "2020-01-01",
        },
        headers=headers_a,
    )
    exp_id = exp_res.json()["id"]

    # User B attempts to delete User A's skill -> 403 Forbidden
    del_skill = client.delete(
        f"/api/v1/profile/skills/{skill_assoc_id}", headers=headers_b
    )
    assert del_skill.status_code == status.HTTP_403_FORBIDDEN

    # User B attempts to delete User A's experience -> 403 Forbidden
    del_exp = client.delete(
        f"/api/v1/profile/experience/{exp_id}", headers=headers_b
    )
    assert del_exp.status_code == status.HTTP_403_FORBIDDEN


def test_profile_completeness_endpoint(client: TestClient):
    """Verify /profile/completeness returns breakdown and missing sections."""
    headers = _get_auth_header(client, "complete_user@example.com")

    res = client.get("/api/v1/profile/completeness", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "profile_completion_percent" in data
    assert "missing_sections" in data
    assert "breakdown" in data
