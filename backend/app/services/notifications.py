"""Notification orchestration.

Persists a Notification + per-channel NotificationDelivery rows, then dispatches
via providers. Dispatch is invoked from Celery tasks so it is never part of the
ticket-creation DB transaction. Includes retry/backoff bookkeeping.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.enums import DeliveryStatus, NotificationChannel
from app.models.notification import Notification, NotificationDelivery
from app.providers.notifications import get_provider
from app.providers.notifications.base import NotificationMessage

log = get_logger(__name__)


async def create_notification(
    session: AsyncSession, *, event_type: str, subject: str, body: str,
    channels: list[NotificationChannel], ticket_id: uuid.UUID | None = None,
    recipient_email: str | None = None, recipient_user_id: uuid.UUID | None = None,
) -> Notification:
    n = Notification(
        event_type=event_type, subject=subject, body=body,
        ticket_id=ticket_id, recipient_email=recipient_email,
        recipient_user_id=recipient_user_id,
    )
    session.add(n)
    await session.flush()
    for ch in channels:
        session.add(NotificationDelivery(notification_id=n.id, channel=ch))
    await session.commit()
    await session.refresh(n)
    return n


async def dispatch_pending(session: AsyncSession, notification_id: uuid.UUID) -> None:
    n = (await session.execute(
        select(Notification).where(Notification.id == notification_id)
    )).scalar_one_or_none()
    if not n:
        return
    deliveries = (await session.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.notification_id == notification_id
        )
    )).scalars().all()
    for d in deliveries:
        if d.status == DeliveryStatus.SENT:
            continue
        to = n.recipient_email or ""
        if d.channel == NotificationChannel.IN_APP:
            d.status = DeliveryStatus.SENT  # persisted row IS the in-app message
            continue
        provider = get_provider(d.channel)
        d.attempts += 1
        result = await provider.send(NotificationMessage(
            to=to, subject=n.subject, body=n.body,
        ))
        if result.ok:
            d.status = DeliveryStatus.SENT
            d.provider_message_id = result.provider_message_id
        else:
            # Bounded retry with backoff handled by the Celery task scheduler.
            d.status = (DeliveryStatus.RETRYING if d.attempts < 5
                        else DeliveryStatus.FAILED)
            d.last_error = result.error
    await session.commit()
