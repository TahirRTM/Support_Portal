"""Celery tasks. Each opens its own async DB session via asyncio.run."""
from __future__ import annotations

import asyncio
import uuid

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.enums import NotificationChannel
from app.services import ai as ai_service
from app.services import notifications as notif_service
from app.workers.celery_app import celery_app

log = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30)
def process_ticket_ai(self, ticket_id: str) -> None:
    """Run AI analysis + acknowledgment. Never fatal to ticket state."""
    async def _job() -> None:
        async with SessionLocal() as session:
            await ai_service.analyze_ticket(session, uuid.UUID(ticket_id))
    try:
        _run(_job())
    except Exception as exc:  # deterministic fallback already covers content;
        log.warning("process_ticket_ai_error", error=str(exc))


@celery_app.task(bind=True, max_retries=5)
def dispatch_notification(self, notification_id: str) -> None:
    async def _job() -> None:
        async with SessionLocal() as session:
            await notif_service.dispatch_pending(session, uuid.UUID(notification_id))
    _run(_job())


@celery_app.task
def sweep_sla() -> None:
    from app.services import sla as sla_service
    async def _job() -> None:
        async with SessionLocal() as session:
            await sla_service.sweep(session)
    _run(_job())


@celery_app.task
def retry_failed_notifications() -> None:
    from sqlalchemy import select
    from app.models.enums import DeliveryStatus
    from app.models.notification import NotificationDelivery
    async def _job() -> None:
        async with SessionLocal() as session:
            rows = (await session.execute(
                select(NotificationDelivery.notification_id).where(
                    NotificationDelivery.status == DeliveryStatus.RETRYING
                )
            )).scalars().all()
            for nid in set(rows):
                await notif_service.dispatch_pending(session, nid)
    _run(_job())
