"""Standard SMTP email provider implementation."""

from email.message import EmailMessage
import logging
import smtplib
import socket
from typing import Optional
import uuid

from app.notifications.payload import DeliveryResult
from app.notifications.providers.base import EmailProvider

logger = logging.getLogger(__name__)


class SMTPProvider(EmailProvider):
    """Production email provider dispatching via standard SMTP."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: str = "alerts@jobwatch.ai",
        from_name: str = "JobWatch AI",
        use_tls: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
        self.timeout = timeout

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> DeliveryResult:
        """Connect to SMTP server and send MIME message."""
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = f"{recipient_name} <{to_email}>" if recipient_name else to_email
        msg.set_content(text_body)

        if html_body:
            msg.add_alternative(html_body, subtype="html")

        message_id = f"smtp-{uuid.uuid4().hex[:12]}"
        msg["Message-ID"] = f"<{message_id}@{self.host}>"

        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            logger.info("notification.email.sent to=%s msg_id=%s", to_email, message_id)
            return DeliveryResult(
                success=True,
                provider_message_id=message_id,
            )

        except (
            smtplib.SMTPConnectError,
            smtplib.SMTPServerDisconnected,
            socket.timeout,
            TimeoutError,
            ConnectionRefusedError,
            OSError,
        ) as e:
            logger.warning("notification.email.transient_failure to=%s error=%s", to_email, e)
            return DeliveryResult(
                success=False,
                error_message=f"Transient SMTP error: {str(e)}",
                is_transient=True,
            )

        except (
            smtplib.SMTPAuthenticationError,
            smtplib.SMTPRecipientsRefused,
            smtplib.SMTPSenderRefused,
            smtplib.SMTPDataError,
            smtplib.SMTPException,
        ) as e:
            logger.error("notification.email.permanent_failure to=%s error=%s", to_email, e)
            return DeliveryResult(
                success=False,
                error_message=f"Permanent SMTP error: {str(e)}",
                is_transient=False,
            )

        except Exception as e:
            logger.error("notification.email.unexpected_failure to=%s error=%s", to_email, e)
            return DeliveryResult(
                success=False,
                error_message=f"Unexpected email error: {str(e)}",
                is_transient=False,
            )
