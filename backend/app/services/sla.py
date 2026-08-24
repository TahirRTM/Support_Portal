"""SLA engine: compute due dates, detect breaches, drive escalation.

Business hours aware (Mon-Fri, configurable window). Called on ticket creation
to set due dates and periodically by Celery Beat to flag breaches.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TicketStatus
from app.models.ticket import Ticket

BUSINESS_START = time(9, 0)
BUSINESS_END = time(17, 0)
WORKING_WEEKDAYS = {0, 1, 2, 3, 4}  # Mon-Fri


def add_business_minutes(start: datetime, minutes: int) -> datetime:
    """Add SLA minutes, counting only business hours."""
    remaining = minutes
    cursor = start.astimezone(timezone.utc)
    guard = 0
    while remaining > 0 and guard < 100_000:
        guard += 1
        if cursor.weekday() not in WORKING_WEEKDAYS:
            cursor = _next_day_open(cursor)
            continue
        day_start = cursor.replace(hour=BUSINESS_START.hour, minute=BUSINESS_START.minute,
                                   second=0, microsecond=0)
        day_end = cursor.replace(hour=BUSINESS_END.hour, minute=BUSINESS_END.minute,
                                 second=0, microsecond=0)
        if cursor < day_start:
            cursor = day_start
        if cursor >= day_end:
            cursor = _next_day_open(cursor)
            continue
        avail = int((day_end - cursor).total_seconds() // 60)
        if remaining <= avail:
            return cursor + timedelta(minutes=remaining)
        remaining -= avail
        cursor = _next_day_open(cursor)
    return cursor


def _next_day_open(cursor: datetime) -> datetime:
    nxt = (cursor + timedelta(days=1)).replace(
        hour=BUSINESS_START.hour, minute=BUSINESS_START.minute, second=0, microsecond=0)
    while nxt.weekday() not in WORKING_WEEKDAYS:
        nxt += timedelta(days=1)
    return nxt


async def apply_sla(session: AsyncSession, ticket: Ticket) -> None:
    """Set response/resolution due dates from the ticket priority."""
    resp = res = None
    if ticket.priority_id:
        from app.models.reference import Priority
        prio = (await session.execute(
            select(Priority).where(Priority.id == ticket.priority_id)
        )).scalar_one_or_none()
        if prio:
            resp = prio.sla_response_minutes
            res = prio.sla_resolution_minutes
    resp = resp or 240        # default 4 business hours
    res = res or 1920         # default ~ 4 business days
    ticket.sla_response_due_at = add_business_minutes(ticket.created_at, resp)
    ticket.sla_resolution_due_at = add_business_minutes(ticket.created_at, res)
    await session.commit()


async def sweep(session: AsyncSession) -> int:
    """Flag SLA breaches for open tickets. Returns count of newly breached."""
    now = datetime.now(timezone.utc)
    open_states = [TicketStatus.NEW, TicketStatus.OPEN, TicketStatus.IN_PROGRESS,
                   TicketStatus.PENDING_INTERNAL, TicketStatus.REOPENED]
    tickets = (await session.execute(
        select(Ticket).where(Ticket.status.in_(open_states),
                             Ticket.deleted_at.is_(None))
    )).scalars().all()
    breached = 0
    for t in tickets:
        if (not t.sla_response_breached and t.first_response_at is None
                and t.sla_response_due_at and now > t.sla_response_due_at):
            t.sla_response_breached = True
            breached += 1
        if (not t.sla_resolution_breached and t.resolved_at is None
                and t.sla_resolution_due_at and now > t.sla_resolution_due_at):
            t.sla_resolution_breached = True
            breached += 1
    await session.commit()
    return breached
