"""Tests for CareerSource dev sync API endpoint."""

import uuid
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.career_source import CareerSource


def test_sync_source_endpoint_success(client: TestClient, db_session: Session, monkeypatch):
    """Verify POST /api/v1/sources/{id}/sync triggers ingestion and returns summary."""
    company = Company(
        id=uuid.uuid4(),
        name="API Test Corp",
        slug=f"api-test-{uuid.uuid4().hex[:8]}",
        website_url="https://apitest.example.com",
    )
    db_session.add(company)
    db_session.commit()

    source = CareerSource(
        id=uuid.uuid4(),
        company_id=company.id,
        name="API Test Greenhouse",
        source_type="greenhouse",
        base_url="https://boards.greenhouse.io/apitest",
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()

    # Mock ConnectorHttpClient.request using monkeypatch
    async def mock_request(self, method, url, **kwargs):
        return httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 9901,
                        "title": "Cloud Architect",
                        "absolute_url": "https://boards.greenhouse.io/apitest/jobs/9901",
                        "location": {"name": "Remote"},
                    }
                ]
            },
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr("app.connectors.http.ConnectorHttpClient.request", mock_request)

    response = client.post(f"/api/v1/sources/{source.id}/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == str(source.id)
    assert data["jobs_fetched"] == 1
    assert data["jobs_persisted"] == 1
    assert data["errors"] == []


def test_sync_source_endpoint_not_found(client: TestClient):
    """Verify 400 response for non-existent CareerSource."""
    random_id = uuid.uuid4()
    response = client.post(f"/api/v1/sources/{random_id}/sync")
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]
