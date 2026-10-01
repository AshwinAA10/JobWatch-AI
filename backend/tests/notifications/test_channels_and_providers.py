"""Tests for Email and Webhook channels, fake providers, templates, and HTTP error classification."""

import uuid
import httpx
import pytest

from app.notifications.channels.email import EmailChannel
from app.notifications.channels.webhook import WebhookChannel
from app.notifications.payload import NotificationPayload
from app.notifications.providers.email_fake import FakeEmailProvider
from app.notifications.providers.webhook_fake import FakeWebhookProvider
from app.notifications.providers.webhook_http import HTTPWebhookProvider


def test_fake_email_provider_success():
    """Verify fake email provider records sent messages."""
    provider = FakeEmailProvider()
    result = provider.send_email(
        to_email="dev@example.com",
        subject="New Match",
        text_body="Match body",
        html_body="<p>Match body</p>",
        recipient_name="Dev User",
    )

    assert result.success is True
    assert result.provider_message_id is not None
    assert len(provider.sent_messages) == 1
    assert provider.sent_messages[0].to_email == "dev@example.com"
    assert provider.sent_messages[0].subject == "New Match"


def test_fake_email_provider_errors():
    """Verify transient vs permanent failure simulation in email provider."""
    # Transient error
    transient_provider = FakeEmailProvider(should_fail=True, failure_type="transient")
    res1 = transient_provider.send_email(
        to_email="test@example.com",
        subject="Subject",
        text_body="Body",
    )
    assert res1.success is False
    assert res1.is_transient is True

    # Permanent error
    perm_provider = FakeEmailProvider(should_fail=True, failure_type="permanent")
    res2 = perm_provider.send_email(
        to_email="test@example.com",
        subject="Subject",
        text_body="Body",
    )
    assert res2.success is False
    assert res2.is_transient is False


def test_fake_webhook_provider_success_and_hmac():
    """Verify fake webhook provider records payloads and secrets."""
    provider = FakeWebhookProvider()
    payload = {"event": "NEW_MATCH", "score": 85}

    result = provider.send_webhook(
        url="https://api.example.com/webhook",
        payload=payload,
        secret="test-secret-key",
    )

    assert result.success is True
    assert len(provider.sent_webhooks) == 1
    call = provider.sent_webhooks[0]
    assert call.url == "https://api.example.com/webhook"
    assert call.payload == payload
    assert call.secret == "test-secret-key"


def test_fake_webhook_provider_status_codes():
    """Verify fake webhook provider error classification."""
    # 429 Rate limited -> transient with Retry-After
    rate_limited_provider = FakeWebhookProvider(
        should_fail=True,
        failure_type="transient",
        status_code=429,
        retry_after=30.0,
    )
    res429 = rate_limited_provider.send_webhook("https://api.example.com/webhook", {})
    assert res429.success is False
    assert res429.is_transient is True
    assert res429.retry_after_seconds == 30.0

    # 500 Server error -> transient
    server_error_provider = FakeWebhookProvider(
        should_fail=True,
        failure_type="transient",
        status_code=500,
    )
    res500 = server_error_provider.send_webhook("https://api.example.com/webhook", {})
    assert res500.success is False
    assert res500.is_transient is True

    # 400 Bad request -> permanent
    bad_req_provider = FakeWebhookProvider(
        should_fail=True,
        failure_type="permanent",
        status_code=400,
    )
    res400 = bad_req_provider.send_webhook("https://api.example.com/webhook", {})
    assert res400.success is False
    assert res400.is_transient is False


def test_email_channel_missing_recipient():
    """Verify EmailChannel fails permanently when recipient email is absent."""
    channel = EmailChannel(FakeEmailProvider())
    payload = NotificationPayload(
        notification_id=uuid.uuid4(),
        delivery_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        event_type="NEW_MATCH",
        title="Title",
        body="Body",
        recipient_email=None,  # Missing
    )
    result = channel.send(payload)
    assert result.success is False
    assert result.is_transient is False
    assert "verified recipient email" in result.error_message


def test_email_channel_renders_templates_and_sends():
    """Verify EmailChannel renders job details and reasons into the email."""
    provider = FakeEmailProvider()
    channel = EmailChannel(provider)

    payload = NotificationPayload(
        notification_id=uuid.uuid4(),
        delivery_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        event_type="NEW_MATCH",
        title="Staff Engineer at Stripe",
        body="Body",
        recipient_email="candidate@example.com",
        recipient_name="Alice Smith",
        job_data={
            "title": "Staff Engineer",
            "company_name": "Stripe",
            "location": "Remote",
            "workplace_type": "REMOTE",
            "application_url": "https://stripe.com/jobs/123",
        },
        match_data={
            "score": 91.0,
            "reasons": ["Extensive distributed systems experience", "Python expertise"],
            "missing_criteria": ["Ruby on Rails"],
        },
    )

    result = channel.send(payload)
    assert result.success is True
    assert len(provider.sent_messages) == 1

    sent = provider.sent_messages[0]
    assert sent.to_email == "candidate@example.com"
    assert "91% Match" in sent.subject
    assert "Staff Engineer at Stripe" in sent.subject
    assert "Alice Smith" in sent.text_body
    assert "https://stripe.com/jobs/123" in sent.text_body
    assert "Ruby on Rails" in sent.text_body


def test_webhook_channel_missing_url():
    """Verify WebhookChannel fails permanently when webhook URL is missing."""
    channel = WebhookChannel(FakeWebhookProvider())
    payload = NotificationPayload(
        notification_id=uuid.uuid4(),
        delivery_id=uuid.uuid4(),
        profile_id=uuid.uuid4(),
        event_type="NEW_MATCH",
        title="Title",
        body="Body",
        webhook_url=None,  # Missing
    )
    result = channel.send(payload)
    assert result.success is False
    assert result.is_transient is False
    assert "webhook URL configured" in result.error_message


from unittest.mock import patch


def test_http_webhook_provider_retry_after_header():
    """Verify HTTPWebhookProvider parses Retry-After header and classifies 429 as transient."""
    provider = HTTPWebhookProvider()

    mock_resp = httpx.Response(
        status_code=429,
        headers={"Retry-After": "45"},
        request=httpx.Request("POST", "https://api.example.com/hook"),
    )

    with patch("app.notifications.providers.webhook_http.validate_webhook_url_ssrf"):
        with patch.object(httpx.Client, "post", return_value=mock_resp):
            result = provider.send_webhook("https://api.example.com/hook", {"data": 123})

    assert result.success is False
    assert result.is_transient is True
    assert result.retry_after_seconds == 45.0
