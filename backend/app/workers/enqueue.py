"""Best-effort task enqueue.

In environments without a running broker the .delay() call may fail; we log and
continue. Ticket creation must never fail because a queue is unavailable.
"""
from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)


def enqueue_ticket_ai(ticket_id: str) -> None:
    try:
        from app.workers.tasks import process_ticket_ai
        process_ticket_ai.delay(ticket_id)
    except Exception as exc:
        log.warning("enqueue_ai_failed", error=str(exc), ticket_id=ticket_id)


def enqueue_notification(notification_id: str) -> None:
    try:
        from app.workers.tasks import dispatch_notification
        dispatch_notification.delay(notification_id)
    except Exception as exc:
        log.warning("enqueue_notification_failed", error=str(exc))
