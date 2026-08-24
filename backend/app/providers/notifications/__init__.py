from __future__ import annotations

from app.models.enums import NotificationChannel
from app.providers.notifications.base import NotificationProvider
from app.providers.notifications.email import EmailProvider
from app.providers.notifications.inapp import InAppProvider
from app.providers.notifications.pushover import PushoverProvider
from app.providers.notifications.whatsapp import WhatsAppProvider

_REGISTRY: dict[NotificationChannel, NotificationProvider] = {
    NotificationChannel.EMAIL: EmailProvider(),
    NotificationChannel.WHATSAPP: WhatsAppProvider(),
    NotificationChannel.PUSHOVER: PushoverProvider(),
    NotificationChannel.IN_APP: InAppProvider(),
}


def get_provider(channel: NotificationChannel) -> NotificationProvider:
    return _REGISTRY[channel]
