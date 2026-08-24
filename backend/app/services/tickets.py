"""Core ticket service: creation, tracking, replies, status timeline.

Security invariants enforced here:
- Case Number alone never grants access (access requires a verified client session).
- Client-visible queries filter messages/attachments to PUBLIC only.
- Ticket creation commits BEFORE any AI/notification side effects are queued.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.enums import AuthorType, MessageVisibility, TicketStatus
from app.models.ticket import (
    Ticket, TicketAttachment, TicketMessage, TicketStatusEvent,
)
from app.schemas.ticket import TicketCreate
from app.security.case_number import generate_case_number, normalize_case_number


async def create_ticket(
    session: AsyncSession, data: TicketCreate, *, source_ip: str | None,
) -> Ticket:
    year = datetime.now(timezone.utc).year
    # Retry on the (astronomically unlikely) case-number collision.
    for _ in range(5):
        case_number = generate_case_number(year)
        ticket = Ticket(
            case_number=case_number,
            client_name=data.name,
            client_email=str(data.email).lower(),
            client_company=data.company,
            client_phone=data.phone,
            subject=data.subject,
            description=data.description,
            category_id=data.category_id,
            priority_id=data.priority_id,
            status=TicketStatus.NEW,
            source_ip=source_ip,
        )
        session.add(ticket)
        # Initial public message mirrors the submitted description.
        session.add(TicketMessage(
            ticket=ticket, author_type=AuthorType.CLIENT,
            author_display=data.name, visibility=MessageVisibility.PUBLIC,
            body=data.description,
        ))
        session.add(TicketStatusEvent(
            ticket=ticket, from_status=None, to_status=TicketStatus.NEW.value,
            note="Ticket created",
        ))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            continue
        await session.refresh(ticket)
        return ticket
    raise RuntimeError("Unable to allocate a unique case number")


async def _get_by_case(session: AsyncSession, case_number: str) -> Ticket | None:
    normalized = normalize_case_number(case_number)
    if not normalized:
        return None
    stmt = select(Ticket).where(
        Ticket.case_number == normalized, Ticket.deleted_at.is_(None)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def find_for_otp(
    session: AsyncSession, case_number: str, email: str,
) -> Ticket | None:
    """Match case+email. Returns None (not error) to avoid enumeration."""
    ticket = await _get_by_case(session, case_number)
    if ticket and ticket.client_email == email.lower():
        return ticket
    return None


async def get_client_view(session: AsyncSession, ticket_id: uuid.UUID) -> Ticket:
    stmt = (
        select(Ticket)
        .where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
        .options(
            selectinload(Ticket.messages),
            selectinload(Ticket.attachments),
            selectinload(Ticket.status_history),
        )
    )
    ticket = (await session.execute(stmt)).scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket not found.")
    return ticket


def public_messages(ticket: Ticket) -> list[TicketMessage]:
    return sorted(
        [m for m in ticket.messages if m.visibility == MessageVisibility.PUBLIC],
        key=lambda m: m.created_at,
    )


def public_attachments(ticket: Ticket) -> list[TicketAttachment]:
    return [a for a in ticket.attachments if a.visibility == MessageVisibility.PUBLIC]


async def add_client_reply(
    session: AsyncSession, ticket: Ticket, body: str,
) -> TicketMessage:
    msg = TicketMessage(
        ticket_id=ticket.id, author_type=AuthorType.CLIENT,
        author_display=ticket.client_name, visibility=MessageVisibility.PUBLIC,
        body=body,
    )
    session.add(msg)
    if ticket.status in (TicketStatus.PENDING_CLIENT, TicketStatus.RESOLVED):
        old = ticket.status
        ticket.status = TicketStatus.OPEN
        session.add(TicketStatusEvent(
            ticket_id=ticket.id, from_status=old.value,
            to_status=TicketStatus.OPEN.value, note="Client replied",
        ))
    await session.commit()
    await session.refresh(msg)
    return msg
