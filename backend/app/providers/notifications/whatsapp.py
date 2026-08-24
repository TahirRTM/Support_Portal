"""WhatsApp provider abstraction (vendor-agnostic HTTP)."""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.notifications.base import (
    NotificationMessage, NotificationProvider, SendResult,
)

log = get_logger(__name__)


class WhatsAppProvider(NotificationProvider):
    """Generic provider: posts to a configured vendor endpoint with a bearer key.

    Concrete vendor (Meta Cloud API, Twilio, etc.) is selected by config; the
    request shape here is the common denominator and can be adapted per vendor.
    """
    channel = "whatsapp"

    async def send(self, msg: NotificationMessage) -> SendResult:
        s = get_settings()
        if not s.whatsapp_api_key:
            log.info("whatsapp_skipped_no_key", to=msg.to)
            return SendResult(ok=False, error="whatsapp_not_configured")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://graph.facebook.com/v19.0/{s.whatsapp_from}/messages",
                    headers={"Authorization": f"Bearer {s.whatsapp_api_key}"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": msg.to,
                        "type": "text",
                        "text": {"body": msg.body},
                    },
                )
                resp.raise_for_status()
                mid = resp.json().get("messages", [{}])[0].get("id")
            return SendResult(ok=True, provider_message_id=mid)
        except Exception as exc:  # pragma: no cover - network dependent
            log.warning("whatsapp_send_failed", error=str(exc))
            return SendResult(ok=False, error=str(exc)[:400])
