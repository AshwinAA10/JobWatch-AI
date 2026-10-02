"""Structured logging, sensitive data redaction, and request context tracking."""

import contextvars
import json
import logging
import re
import sys
from typing import Any, Dict, Optional

# Context variable storing request ID for correlation across log records
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

# Patterns matching sensitive data that should NEVER appear in logs
SENSITIVE_PATTERNS = [
    (re.compile(r"(bearer\s+)[a-zA-Z0-9_\-\.]+", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    (re.compile(r'(password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r"\1[REDACTED_PASSWORD]\3"),
    (re.compile(r'(secret["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r"\1[REDACTED_SECRET]\3"),
    (re.compile(r'(api[_\-]?key["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r"\1[REDACTED_KEY]\3"),
    (re.compile(r"(postgresql(?:\+psycopg)?://[^:]+:)([^@]+)(@)", re.IGNORECASE), r"\1[REDACTED_DB_PASS]\3"),
]


def redact_sensitive_str(text: str) -> str:
    """Sanitize sensitive strings (passwords, tokens, database credentials)."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


class SensitiveDataFilter(logging.Filter):
    """Logging filter to redact sensitive tokens, credentials, and parameters."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_str(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_sensitive_str(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(redact_sensitive_str(a) if isinstance(a, str) else a for a in record.args)
        return True


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured logs with correlation request_id."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if req_id:
            log_entry["request_id"] = req_id
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(debug: bool = False, json_logs: bool = False) -> None:
    """Configure root and application loggers."""
    root_logger = logging.getLogger()
    log_level = logging.DEBUG if debug else logging.INFO
    root_logger.setLevel(log_level)

    # Avoid adding duplicate handlers on multiple calls
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.addFilter(SensitiveDataFilter())

    if json_logs:
        handler.setFormatter(StructuredFormatter())
    else:
        standard_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(standard_format))

    root_logger.addHandler(handler)
