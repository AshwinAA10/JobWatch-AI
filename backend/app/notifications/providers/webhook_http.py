"""HTTP Webhook provider with SSRF defense, HMAC signatures, and retry classification."""

import hashlib
import hmac
import ipaddress
import json
import logging
import socket
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import httpx

from app.notifications.exceptions import PermanentDeliveryError, SSRFSecurityError, TransientDeliveryError
from app.notifications.payload import DeliveryResult
from app.notifications.providers.base import WebhookProvider

logger = logging.getLogger(__name__)

BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
MAX_RETRY_AFTER_SECONDS = 3600.0


def validate_webhook_url_ssrf(url: str) -> None:
    """Validate webhook URL against SSRF vulnerabilities and private network destinations."""
    if not url or not isinstance(url, str):
        raise SSRFSecurityError("Webhook URL must be a non-empty string.")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise SSRFSecurityError(f"Disallowed URL scheme '{parsed.scheme}'. Only http and https permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("Webhook URL has no valid hostname.")

    if hostname.lower() in BLOCKED_HOSTNAMES:
        raise SSRFSecurityError(f"Webhook destination '{hostname}' is not permitted.")

    # Resolve IP addresses and verify against private/local/metadata ranges
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFSecurityError(f"Could not resolve webhook host '{hostname}': {e}")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or str(ip) == "169.254.169.254"
            ):
                raise SSRFSecurityError(
                    f"Webhook destination resolves to prohibited internal address: {ip_str}"
                )
        except ValueError:
            raise SSRFSecurityError(f"Invalid resolved IP address: {ip_str}")


class HTTPWebhookProvider(WebhookProvider):
    """Production webhook provider executing outbound JSON HTTP POST requests."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> DeliveryResult:
        """Validate URL for SSRF, sign payload, and POST JSON."""
        # 1. SSRF Safety Check
        try:
            validate_webhook_url_ssrf(url)
        except SSRFSecurityError as e:
            logger.error("notification.webhook.ssrf_blocked url=%s error=%s", url, e)
            return DeliveryResult(
                success=False,
                error_message=str(e),
                is_transient=False,
            )
        except PermanentDeliveryError as e:
            return DeliveryResult(
                success=False,
                error_message=str(e),
                is_transient=False,
            )

        # 2. Serialize payload and sign with HMAC-SHA256 if secret provided
        body_bytes = json.dumps(payload, default=str).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JobWatchAI-Webhook/0.1.0",
        }

        if secret:
            signature = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            headers["X-JobWatch-Signature"] = f"sha256={signature}"

        # 3. Execute HTTP POST
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, content=body_bytes, headers=headers)

            status_code = response.status_code

            # Success
            if 200 <= status_code < 300:
                logger.info("notification.webhook.success url=%s status=%d", url, status_code)
                return DeliveryResult(
                    success=True,
                    provider_message_id=f"http-{status_code}",
                )

            # Transient errors: 429 Too Many Requests or 5xx Server Errors
            if status_code == 429 or 500 <= status_code < 600:
                retry_after_sec = self._parse_retry_after(response.headers.get("Retry-After"))
                logger.warning(
                    "notification.webhook.transient_failure url=%s status=%d retry_after=%s",
                    url,
                    status_code,
                    retry_after_sec,
                )
                return DeliveryResult(
                    success=False,
                    error_message=f"Webhook server returned transient HTTP {status_code}",
                    is_transient=True,
                    retry_after_seconds=retry_after_sec,
                )

            # Permanent errors: other 4xx client errors
            logger.error("notification.webhook.permanent_failure url=%s status=%d", url, status_code)
            return DeliveryResult(
                success=False,
                error_message=f"Webhook server returned permanent client error HTTP {status_code}",
                is_transient=False,
            )

        except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as e:
            logger.warning("notification.webhook.network_error url=%s error=%s", url, e)
            return DeliveryResult(
                success=False,
                error_message=f"Webhook network error: {str(e)}",
                is_transient=True,
            )
        except Exception as e:
            logger.error("notification.webhook.unexpected_error url=%s error=%s", url, e)
            return DeliveryResult(
                success=False,
                error_message=f"Unexpected webhook error: {str(e)}",
                is_transient=False,
            )

    @staticmethod
    def _parse_retry_after(header_val: Optional[str]) -> Optional[float]:
        """Parse Retry-After header as integer/float seconds, capped to max ceiling."""
        if not header_val:
            return None
        try:
            val = float(header_val.strip())
            return min(max(0.0, val), MAX_RETRY_AFTER_SECONDS)
        except ValueError:
            return None
