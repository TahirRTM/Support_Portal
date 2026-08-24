"""Pushover provider."""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.notifications.base import (
    NotificationMessage, NotificationProvider, SendResult,
)

log = get_logger(__name__)


class PushoverProvider(NotificationProvider):
    channel = "pushover"

    async def send(self, msg: NotificationMessage) -> SendResult:
        s = get_settings()
        if not (s.pushover_token and s.pushover_user_key):
            log.info("pushover_skipped_no_config")
            return SendResult(ok=False, error="pushover_not_configured")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.pushover.net/1/messages.json",
                    data={
                        "token": s.pushover_token,
                        "user": s.pushover_user_key,
                        "title": msg.subject,
                        "message": msg.body,
                    },
                )
                resp.raise_for_status()
            return SendResult(ok=True)
        except Exception as exc:  # pragma: no cover - network dependent
            log.warning("pushover_send_failed", error=str(exc))
            return SendResult(ok=False, error=str(exc)[:400])
