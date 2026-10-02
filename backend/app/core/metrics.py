"""Lightweight in-memory application metrics tracker for operational visibility."""

import threading
import time
from collections import defaultdict
from typing import Any, Dict


class MetricsRegistry:
    """Thread-safe in-memory metrics registry for HTTP and subsystem telemetry."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._request_count = defaultdict(int)
        self._request_errors = defaultdict(int)
        self._request_latency_sum = defaultdict(float)
        self._connector_syncs = defaultdict(int)
        self._connector_errors = defaultdict(int)
        self._ai_requests = defaultdict(int)
        self._ai_errors = defaultdict(int)
        self._notification_attempts = defaultdict(int)
        self._notification_failures = defaultdict(int)
        self._start_time = time.time()

    def record_http_request(self, method: str, path_template: str, status_code: int, duration_ms: float) -> None:
        """Record an incoming HTTP request using bounded label cardinality."""
        key = f"{method} {path_template} {status_code}"
        with self._lock:
            self._request_count[key] += 1
            self._request_latency_sum[key] += duration_ms
            if status_code >= 400:
                self._request_errors[key] += 1

    def record_connector_sync(self, connector_type: str, success: bool) -> None:
        """Record a connector ingestion attempt."""
        with self._lock:
            self._connector_syncs[connector_type] += 1
            if not success:
                self._connector_errors[connector_type] += 1

    def record_ai_request(self, operation: str, success: bool) -> None:
        """Record an AI service call (extraction, embedding, etc)."""
        with self._lock:
            self._ai_requests[operation] += 1
            if not success:
                self._ai_errors[operation] += 1

    def record_notification(self, channel: str, success: bool) -> None:
        """Record a notification delivery attempt."""
        with self._lock:
            self._notification_attempts[channel] += 1
            if not success:
                self._notification_failures[channel] += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Return a snapshot dictionary of collected metrics."""
        with self._lock:
            total_requests = sum(self._request_count.values())
            total_errors = sum(self._request_errors.values())
            uptime_seconds = round(time.time() - self._start_time, 2)

            return {
                "uptime_seconds": uptime_seconds,
                "http": {
                    "total_requests": total_requests,
                    "total_errors": total_errors,
                    "requests_by_endpoint": dict(self._request_count),
                    "errors_by_endpoint": dict(self._request_errors),
                },
                "connectors": {
                    "sync_attempts": dict(self._connector_syncs),
                    "sync_failures": dict(self._connector_errors),
                },
                "ai": {
                    "requests": dict(self._ai_requests),
                    "failures": dict(self._ai_errors),
                },
                "notifications": {
                    "attempts": dict(self._notification_attempts),
                    "failures": dict(self._notification_failures),
                },
            }


# Global metrics registry instance
metrics = MetricsRegistry()
