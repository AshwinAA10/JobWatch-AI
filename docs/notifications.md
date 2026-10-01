# JobWatch AI — Notification & Alerting System (Phase 8)

## 1. Subsystem Overview

Phase 8 introduces a provider-independent notification subsystem engineered to deliver timely, relevant alerts to candidates when monitored career portals detect positions matching their preferences.

### Core Architectural Principle

Notifications operate strictly as downstream consumers of matching and system events. Lower-level ingestion pipelines (connectors, monitoring, deduplication, matching engines, and AI enrichment services) never invoke delivery infrastructure directly.

```text
                     JobWatch AI Intelligence Pipeline
                                     │
                     Ingestion & Career Source Monitoring
                                     │
                                     ▼
                           Canonical Deduplication
                                     │
                                     ▼
                        Deterministic & Hybrid Matching
                                     │
                                     ▼
                               Match Event
                                     │
                                     ▼
                        NotificationService (Eligibility)
                                     │
               ┌─────────────────────┼─────────────────────┐
               ▼                                           ▼
      Score Threshold Filter                       Candidate Preferences
   (min_score >= preference)                     (email_enabled, webhook_enabled)
               │                                           │
               └─────────────────────┬─────────────────────┘
                                     ▼
                          Hourly Flood Protection
                        (sent_last_hour < max_per_hour)
                                     │
                                     ▼
                         Canonical Idempotency Key
             sha256(profile_id + event_type + canonical_job_id + version)
                                     │
                                     ▼
                                Notification
                          (Persistent Record: PENDING)
                                     │
                                     ▼
                           NotificationDelivery
                        (Per-Channel Queued Attempt)
                                     │
                                     ▼
                         NotificationDeliveryWorker
                         (Atomic Claim & Backoff)
                                     │
                      ┌──────────────┴──────────────┐
                      ▼                             ▼
                 EmailChannel                 WebhookChannel
                      │                             │
                EmailProvider                WebhookProvider
               (SMTP / Fake)               (HTTP POST / Fake)
                      │                             │
                      └──────────────┬──────────────┘
                                     ▼
                          Delivery Status Tracking
                 (SENT / RETRYING / FAILED / CANCELLED)
```

---

## 2. Notification Types & Events

| Event Type | Trigger Criteria | Description |
|---|---|---|
| `NEW_MATCH` | `score >= minimum_match_score` | Standard notification when a newly detected job satisfies candidate criteria. |
| `HIGH_QUALITY_MATCH` | `score >= 85.0%` | Prominent alert when a position exhibits exceptional criteria alignment. |
| `MONITORING_FAILURE` | System alerting | Reserved for infrastructure error events. |

---

## 3. Multi-Channel Architecture

The notification layer provides pluggable channel abstractions:

### A. Email Channel (`EmailChannel`)
- **Provider Abstraction**: `EmailProvider` base interface with `SMTPProvider` and `FakeEmailProvider`.
- **Content Rendering**: High-fidelity plain text and HTML templates rendering job title, company, location, workplace type, match score, key matched criteria, missing requirements, and canonical application link.
- **Privacy**: Only sends to authorized candidate account email (`CandidateProfile.user.email`). Unverified emails can be enforced via `EMAIL_REQUIRE_VERIFIED`.

### B. Webhook Channel (`WebhookChannel`)
- **Provider Abstraction**: `WebhookProvider` base interface with `HTTPWebhookProvider` and `FakeWebhookProvider`.
- **Payload**: Standard JSON structure versioned at `v1`, containing sanitized job details and match scores.
- **HMAC Signatures**: Automatically attaches `X-JobWatch-Signature-256` computed as `sha256(hmac(payload, secret))` when a secret is configured.
- **SSRF Defense**: Strict validation rejecting loopback (`127.0.0.1`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local / cloud metadata endpoints (`169.254.169.254`), non-HTTP/HTTPS schemes, and unresolvable hostnames.

---

## 4. Idempotency & Duplicate Prevention

Duplicate alerts from repeated monitoring runs or portal reposts are completely prevented:
1. **Canonical Job Identity Binding**: When a job has `canonical_job_id` set (via Phase 4 deduplication), the notification binds to `canonical_job_id` rather than the portal-specific job ID. Multiple postings of the same role across Greenhouse, Lever, or Workday generate exactly one candidate alert.
2. **Deterministic Hash Key**:
   $$\text{idempotency\_key} = \text{SHA256}(\text{profile\_id} : \text{event\_type} : \text{job\_id} : \text{scoring\_version})$$
3. **Database Unique Constraint**: `uq_notifications_idempotency_key` guarantees database-level uniqueness across concurrent workers.

---

## 5. Delivery Worker, Retries & Stale Recovery

### Atomic Claiming
Workers prevent duplicate concurrent sends by atomically transitioning `PENDING` or eligible `RETRYING` records into `PROCESSING`:
```sql
UPDATE notification_deliveries
SET status = 'PROCESSING', updated_at = NOW()
WHERE id = :id AND (status = 'PENDING' OR (status = 'RETRYING' AND next_retry_at <= NOW()));
```

### Bounded Exponential Backoff
- **Transient Failures** (e.g. SMTP timeout, HTTP 429, HTTP 5xx, network drops):
  - Increments `attempt_count`.
  - Computes backoff delay: $\text{delay} = 60 \times 2^{\text{attempt} - 1}$ seconds (capped at 3600s).
  - Respects HTTP `Retry-After` headers if returned by webhook endpoints.
  - Transitions to `RETRYING`.
- **Permanent Failures** (e.g. invalid URL, missing email, HTTP 4xx client errors):
  - Transitions immediately to `FAILED` without retrying.
- **Max Attempt Exhaustion**: When `attempt_count >= max_attempts`, transitions to `FAILED`.

### Stale Processing Recovery
Deliveries stuck in `PROCESSING` longer than `NOTIFICATION_PROCESSING_TIMEOUT_SECONDS` (default: 600s) due to worker crashes are automatically reset to `RETRYING` (or `FAILED` if attempts are exhausted).

---

## 6. Immediate Unsubscribe & Flood Protection

- **Immediate Cancellation**: Updating preferences to disable a channel (`email_enabled=False` or `webhook_enabled=False`) immediately cancels all pending and retrying deliveries for that candidate on that channel.
- **Hourly Rate Limiting**: Candidates can specify `max_per_hour` (default: 10). If the candidate has already received that number of alerts within the past 60 minutes, subsequent matches are suppressed with structured logging.

---

## 7. Security & Isolation

- **Zero Secret Exposure**: Webhook secrets are masked (`"********"`) in all API responses.
- **Candidate Isolation**: All notification queries and read state modifications strictly verify `notification.profile_id == current_user.profile.id`. Any attempt to access or modify another candidate's notification returns `403 Forbidden`.
- **SSRF Protection**: Prohibits loopback, internal IP ranges, and AWS/GCP metadata endpoints (`169.254.169.254`).
- **Failure Isolation**: Notification delivery failures never disrupt job ingestion, deduplication, or matching pipeline runs.

---

## 8. Configuration Reference

```ini
# Phase 8: Notification & Alerting Settings
NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=false
EMAIL_PROVIDER=smtp
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=alerts@jobwatch.ai
SMTP_FROM_NAME=JobWatch AI
SMTP_USE_TLS=true
SMTP_TIMEOUT_SECONDS=10.0
EMAIL_REQUIRE_VERIFIED=false
WEBHOOK_NOTIFICATIONS_ENABLED=false
WEBHOOK_TIMEOUT_SECONDS=10.0
NOTIFICATION_MAX_RETRIES=4
NOTIFICATION_PROCESSING_TIMEOUT_SECONDS=600
NOTIFICATION_HOURLY_RATE_LIMIT=10
NOTIFICATION_DEFAULT_MIN_SCORE=75.0
```
