"""Admin/support ticket management. All routes require staff permissions."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.dependencies import db_session, require_permission
from app.models.enums import AuthorType, MessageVisibility, TicketStatus
from app.models.ticket import Ticket, TicketMessage, TicketStatusEvent
from app.schemas.admin_ticket import (
    AdminMessage, AdminTicketDetail, AdminTicketRow, AssignChange,
    FieldChange, StaffMessageIn, StatusChange,
)
from app.schemas.common import Page

router = APIRouter(prefix="/admin/tickets", tags=["admin-tickets"])


async def _get(session: AsyncSession, ticket_id: uuid.UUID, *, with_messages=False) -> Ticket:
    stmt = select(Ticket).where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
    if with_messages:
        stmt = stmt.options(selectinload(Ticket.messages))
    ticket = (await session.execute(stmt)).scalar_one_or_none()
    if not ticket:
        raise NotFoundError("Ticket not found.")
    return ticket


@router.get("", response_model=Page[AdminTicketRow])
async def list_tickets(
    session: AsyncSession = Depends(db_session),
    user=Depends(require_permission("ticket.read")),
    q: str | None = Query(default=None, max_length=200),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    assigned_agent_id: uuid.UUID | None = None,
    overdue: bool | None = None,
    unassigned: bool | None = None,
    sort: str = Query(default="created_desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
) -> Page[AdminTicketRow]:
    conds = [Ticket.deleted_at.is_(None)]
    if status_filter:
        conds.append(Ticket.status == status_filter)
    if assigned_agent_id:
        conds.append(Ticket.assigned_agent_id == assigned_agent_id)
    if unassigned:
        conds.append(Ticket.assigned_agent_id.is_(None))
    if overdue:
        conds.append(or_(Ticket.sla_response_breached.is_(True),
                         Ticket.sla_resolution_breached.is_(True)))
    if q:
        like = f"%{q}%"
        conds.append(or_(Ticket.subject.ilike(like), Ticket.case_number.ilike(like),
                         Ticket.client_email.ilike(like), Ticket.client_name.ilike(like)))
    total = (await session.execute(
        select(func.count()).select_from(Ticket).where(*conds)
    )).scalar_one()
    order = {
        "created_desc": Ticket.created_at.desc(),
        "created_asc": Ticket.created_at.asc(),
        "updated_desc": Ticket.updated_at.desc(),
    }.get(sort, Ticket.created_at.desc())
    rows = (await session.execute(
        select(Ticket).where(*conds).order_by(order)
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return Page(items=[AdminTicketRow.model_validate(r) for r in rows],
                total=total, page=page, page_size=page_size)


@router.get("/{ticket_id}", response_model=AdminTicketDetail)
async def ticket_detail(
    ticket_id: uuid.UUID, session: AsyncSession = Depends(db_session),
    user=Depends(require_permission("ticket.read")),
) -> AdminTicketDetail:
    ticket = await _get(session, ticket_id, with_messages=True)
    detail = AdminTicketDetail.model_validate(ticket)
    # Staff see ALL messages (public + internal).
    detail.messages = [AdminMessage.model_validate(m)
                       for m in sorted(ticket.messages, key=lambda x: x.created_at)]
    return detail


@router.post("/{ticket_id}/status", response_model=AdminTicketRow)
async def change_status(
    ticket_id: uuid.UUID, payload: StatusChange,
    session: AsyncSession = Depends(db_session),
    user=Depends(require_permission("ticket.update")),
) -> AdminTicketRow:
    ticket = await _get(session, ticket_id)
    old = ticket.status
    ticket.status = payload.status
    if payload.status == TicketStatus.RESOLVED and ticket.resolved_at is None:
        ticket.resolved_at = datetime.now(timezone.utc)
    session.add(TicketStatusEvent(
        ticket_id=ticket.id, from_status=old.value, to_status=payload.status.value,
        changed_by_user_id=user.id, note=payload.note,
    ))
    await session.commit()
    await session.refresh(ticket)
    return AdminTicketRow.model_validate(ticket)


@router.post("/{ticket_id}/assign", response_model=AdminTicketRow)
async def assign(
    ticket_id: uuid.UUID, payload: AssignChange,
    session: AsyncSession = Depends(db_session),
    user=Depends(require_permission("ticket.assign")),
) -> AdminTicketRow:
    ticket = await _get(session, ticket_id)
    if payload.agent_id is not None:
        ticket.assigned_agent_id = payload.agent_id
    if payload.department_id is not None:
        ticket.department_id = payload.department_id
    if payload.team_id is not None:
        ticket.team_id = payload.team_id
    if ticket.status == TicketStatus.NEW:
        ticket.status = TicketStatus.OPEN
    await session.commit()
    await session.refresh(ticket)
    return AdminTicketRow.model_validate(ticket)


@router.post("/{ticket_id}/fields", response_model=AdminTicketRow)
async def change_fields(
    ticket_id: uuid.UUID, payload: FieldChange,
    session: AsyncSession = Depends(db_session),
    user=Depends(require_permission("ticket.update")),
) -> AdminTicketRow:
    ticket = await _get(session, ticket_id)
    if payload.category_id is not None:
        ticket.category_id = payload.category_id
    if payload.priority_id is not None:
        ticket.priority_id = payload.priority_id
    await session.commit()
    await session.refresh(ticket)
    return AdminTicketRow.model_validate(ticket)


@router.post("/{ticket_id}/messages", response_model=AdminMessage, status_code=201)
async def add_message(
    ticket_id: uuid.UUID, payload: StaffMessageIn,
    session: AsyncSession = Depends(db_session),
    user=Depends(require_permission("ticket.reply")),
) -> AdminMessage:
    ticket = await _get(session, ticket_id)
    visibility = MessageVisibility.INTERNAL if payload.internal else MessageVisibility.PUBLIC
    msg = TicketMessage(
        ticket_id=ticket.id, author_type=AuthorType.AGENT,
        author_user_id=user.id, author_display=user.full_name,
        visibility=visibility, body=payload.body,
    )
    session.add(msg)
    if not payload.internal and ticket.first_response_at is None:
        ticket.first_response_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(msg)
    return AdminMessage.model_validate(msg)
