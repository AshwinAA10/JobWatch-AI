"""Production middleware: Request Correlation IDs, Security Headers, Rate Limiting, and Telemetry."""

import time
import uuid
from collections import defaultdict
from typing import Callable, Dict, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import request_id_ctx
from app.core.metrics import metrics


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ensure every HTTP request has an X-Request-ID and propagate it via contextvars."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        if incoming_id and len(incoming_id.strip()) <= 64:
            req_id = incoming_id.strip()
        else:
            req_id = str(uuid.uuid4())

        # Set request_id in contextvars for logging
        token = request_id_ctx.set(req_id)
        request.state.request_id = req_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach defensive security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter protecting sensitive authentication and resource endpoints."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.settings = get_settings()
        # Storage: endpoint_category:client_ip -> list of epoch timestamps
        self.request_history: Dict[str, list] = defaultdict(list)

    def _clean_and_check(self, key: str, max_requests: int, window_seconds: float = 60.0) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds
        # Evict timestamps older than the sliding window
        self.request_history[key] = [t for t in self.request_history[key] if t > window_start]

        current_count = len(self.request_history[key])
        if current_count >= max_requests:
            remaining = 0
            return False, remaining

        self.request_history[key].append(now)
        remaining = max_requests - (current_count + 1)
        return True, remaining

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        current_settings = get_settings()
        if not current_settings.RATE_LIMIT_ENABLED or current_settings.APP_ENV == "testing":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Sensitive auth routes: tighter limit
        if path in ("/api/v1/auth/login", "/api/v1/auth/register"):
            key = f"auth:{client_ip}"
            allowed, remaining = self._clean_and_check(key, self.settings.AUTH_RATE_LIMIT_PER_MINUTE, 60.0)
            if not allowed:
                req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                            "request_id": req_id,
                        },
                        "detail": "Too many authentication attempts. Please try again in 1 minute.",
                    },
                    headers={"Retry-After": "60", "X-Request-ID": req_id},
                )

        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record HTTP request counts and durations with bounded cardinality."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Generalize path template to avoid high cardinality (e.g. /api/v1/jobs/123 -> /api/v1/jobs)
        path = request.url.path
        parts = [p for p in path.split("/") if p]
        # If last part is UUID or number, collapse it
        if parts and (len(parts[-1]) >= 32 or parts[-1].isdigit()):
            generalized_path = "/" + "/".join(parts[:-1]) + "/{id}"
        else:
            generalized_path = path

        metrics.record_http_request(
            method=request.method,
            path_template=generalized_path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
