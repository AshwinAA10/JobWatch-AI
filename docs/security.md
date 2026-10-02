# JobWatch AI — Security Hardening Guide

## Overview
Phase 11 implements defensive security measures across authentication, authorization, external inputs, network communications, and container execution.

---

## 1. Authentication & Token Security

- **Algorithm Enforcing**: JWT validation explicitly specifies allowed algorithms (`HS256`), rejecting arbitrary `None` or asymmetric algorithm injection.
- **Secret Strength Validation**: In production (`APP_ENV=production`), the system enforces that `JWT_SECRET` has at least 32 characters and rejects default development secrets at startup.
- **Argon2id Password Hashing**: Passwords are saved with salted Argon2id hashes with explicit parameters (`time_cost=3`, `memory_cost=64MB`, `parallelism=4`).
- **No Token Leakage**: JWTs and Bearer tokens are redacted in logs via `SensitiveDataFilter`.

---

## 2. Horizontal Authorization & Profile Isolation

- **Owner-Scoped Queries**: All candidate endpoints (`/api/v1/profile`, `/api/v1/applications`, `/api/v1/saved-jobs`, `/api/v1/notifications`) query records strictly scoped by the authenticated candidate's `profile_id`.
- **Cross-User Rejection**: If Candidate A attempts to access or mutate Candidate B's application or interview, the database query returns 0 rows, triggering an immediate `404 Not Found` or `403 Forbidden`.

---

## 3. Defensive Security Headers

Attached globally via `SecurityHeadersMiddleware`:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: DENY`: Prevents clickjacking attacks by forbidding iframe embedding.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts sensitive URI referrer leakage.
- `X-XSS-Protection: 1; mode=block`: Activates legacy browser anti-XSS filters.

---

## 4. SSRF (Server-Side Request Forgery) Protection

Career portal URLs and webhook notification endpoints validate target destinations:
- **Private IP Blacklisting**: Prohibits localhost, `127.0.0.1`, `169.254.169.254` (cloud metadata), and RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- **Scheme Validation**: Enforces standard `http` or `https` schemes; rejects `file://`, `ftp://`, `javascript:`, or raw sockets.

---

## 5. SQL Injection & XSS Protection

- **Parameterized Queries**: All SQLAlchemy queries use parameterized binds or ORM expressions. Unsafe string interpolation (`f"SELECT ... {user_input}"`) is prohibited.
- **Frontend HTML Sanitization**: Any rich HTML descriptions are passed through `DOMPurify` before DOM rendering.
