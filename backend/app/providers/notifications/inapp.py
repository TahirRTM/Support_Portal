"""In-app provider: persists a Notification row (handled by the service layer).

The actual DB write happens in the notification service; this provider simply
confirms in-app delivery is always available.
"""
from __future__ import annotations

from app.providers.notifications.base import (
    NotificationMessage, NotificationProvider, SendResult,
)


class InAppProvider(NotificationProvider):
    channel = "in_app"

    async def send(self, msg: NotificationMessage) -> SendResult:
        return SendResult(ok=True)
