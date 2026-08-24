"""SMTP email provider. Real integration via aiosmtplib when configured."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.notifications.base import (
    NotificationMessage, NotificationProvider, SendResult,
)

log = get_logger(__name__)


class EmailProvider(NotificationProvider):
    channel = "email"

    async def send(self, msg: NotificationMessage) -> SendResult:
        s = get_settings()
        if not s.smtp_host:
            # No transport configured: report as failed (delivery record captures it)
            # without raising, so the ticket workflow is never impacted.
            log.info("email_skipped_no_smtp", to=msg.to)
            return SendResult(ok=False, error="smtp_not_configured")
        try:
            import aiosmtplib  # type: ignore
            from email.message import EmailMessage

            mail = EmailMessage()
            mail["From"] = s.email_from
            mail["To"] = msg.to
            mail["Subject"] = msg.subject
            mail.set_content(msg.body)
            await aiosmtplib.send(
                mail, hostname=s.smtp_host, port=s.smtp_port,
                username=s.smtp_user or None, password=s.smtp_password or None,
                start_tls=s.smtp_port == 587,
            )
            return SendResult(ok=True)
        except Exception as exc:  # pragma: no cover - network dependent
            log.warning("email_send_failed", error=str(exc))
            return SendResult(ok=False, error=str(exc)[:400])
