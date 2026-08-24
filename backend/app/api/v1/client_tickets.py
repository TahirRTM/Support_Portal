"""Client-facing ticket endpoints (no admin JWT).

Endpoints:
  POST   /support/tickets            create ticket (rate limited + CAPTCHA)
  POST   /support/tickets/otp        request OTP for case+email
  POST   /support/tickets/otp/verify verify OTP -> scoped client session
  GET    /support/tickets/me         view the ticket the session is scoped to
  POST   /support/tickets/me/reply   add a public client reply
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RateLimitError
from app.core.ip import resolve_client_ip
from app.core.logging import get_logger
from app.dependencies import current_client_ticket, db_session
from app.schemas.client_auth import ClientSessionToken, OTPRequest, OTPVerify
from app.schemas.ticket import (
    ClientReply, ClientTicketView, PublicAttachment, PublicMessage,
    StatusEvent, TicketCreate, TicketCreated,
)
from app.services import client_session as cs_service
from app.services import notifications as notif_service
from app.services import sla as sla_service
from app.services import assignment as assign_service
from app.services import tickets as ticket_service
from app.services.rate_limit import check_otp_request, check_ticket_creation
from app.services.turnstile import verify_turnstile
from app.models.enums import NotificationChannel
from app.workers.enqueue import enqueue_notification, enqueue_ticket_ai

log = get_logger(__name__)
router = APIRouter(prefix="/support/tickets", tags=["client"])


@router.post("", response_model=TicketCreated, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate, request: Request,
    session: AsyncSession = Depends(db_session),
) -> TicketCreated:
    ip = resolve_client_ip(request)
    # 1) Rate limit BEFORE doing any expensive work.
    rl = await check_ticket_creation(ip)
    if not rl.allowed:
        raise RateLimitError(rl.retry_after,
                             "Too many ticket submissions. Please try again later.")
    # 2) Server-side CAPTCHA (fails closed).
    await verify_turnstile(payload.captcha_token, remote_ip=ip)
    # 3) Create + COMMIT the ticket. This is the critical transaction.
    ticket = await ticket_service.create_ticket(session, payload, source_ip=ip)
    # 4) Post-commit, non-blocking side effects.
    try:
        await assign_service.route_ticket(session, ticket)
        await sla_service.apply_sla(session, ticket)
    except Exception as exc:
        log.warning("post_commit_routing_failed", error=str(exc))
    # 5) Notifications: create records then enqueue async dispatch.
    try:
        notif = await notif_service.create_notification(
            session, event_type="ticket_received",
            subject=f"[{ticket.case_number}] Support request received",
            body=(f"Your support request has been received.\n"
                  f"Case Number: {ticket.case_number}\n"
                  f"Track it at /support/track using your Case Number and email."),
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            ticket_id=ticket.id, recipient_email=ticket.client_email,
        )
        enqueue_notification(str(notif.id))
    except Exception as exc:
        log.warning("notification_enqueue_failed", error=str(exc))
    # 6) AI acknowledgment/analysis (async, never blocks).
    enqueue_ticket_ai(str(ticket.id))
    return TicketCreated(
        case_number=ticket.case_number, status=ticket.status,
        created_at=ticket.created_at,
    )


@router.post("/otp", status_code=status.HTTP_202_ACCEPTED)
async def request_otp(
    payload: OTPRequest, request: Request,
    session: AsyncSession = Depends(db_session),
) -> dict:
    ip = resolve_client_ip(request)
    ticket = await ticket_service.find_for_otp(session, payload.case_number, str(payload.email))
    generic = {"message": "If the case and email match, a verification code has been sent."}
    if not ticket:
        # Anti-enumeration: identical response whether or not the match exists.
        return generic
    rl = await check_otp_request(str(ticket.id), ip)
    if not rl.allowed:
        raise RateLimitError(rl.retry_after, "Too many code requests.")
    try:
        code = await cs_service.issue_otp(session, ticket)
        notif = await notif_service.create_notification(
            session, event_type="otp",
            subject=f"[{ticket.case_number}] Your verification code",
            body=f"Your verification code is {code}. It expires shortly.",
            channels=[NotificationChannel.EMAIL],
            ticket_id=ticket.id, recipient_email=ticket.client_email,
        )
        enqueue_notification(str(notif.id))
    except RateLimitError:
        raise
    except Exception as exc:
        log.warning("otp_issue_failed", error=str(exc))
    return generic


@router.post("/otp/verify", response_model=ClientSessionToken)
async def verify_otp(
    payload: OTPVerify, session: AsyncSession = Depends(db_session),
) -> ClientSessionToken:
    from app.core.config import get_settings
    from app.core.exceptions import AuthError
    ticket = await ticket_service.find_for_otp(session, payload.case_number, str(payload.email))
    if not ticket:
        raise AuthError("Invalid or expired code.")  # generic
    token = await cs_service.verify_otp(session, ticket, payload.code)
    return ClientSessionToken(
        access_token=token, expires_in=get_settings().client_session_ttl_seconds,
    )


@router.get("/me", response_model=ClientTicketView)
async def view_my_ticket(
    ticket_id: uuid.UUID = Depends(current_client_ticket),
    session: AsyncSession = Depends(db_session),
) -> ClientTicketView:
    ticket = await ticket_service.get_client_view(session, ticket_id)
    return ClientTicketView(
        case_number=ticket.case_number, subject=ticket.subject,
        status=ticket.status, created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages=[PublicMessage.model_validate(m)
                  for m in ticket_service.public_messages(ticket)],
        attachments=[PublicAttachment.model_validate(a)
                     for a in ticket_service.public_attachments(ticket)],
        timeline=[StatusEvent.model_validate(e)
                  for e in sorted(ticket.status_history, key=lambda x: x.created_at)],
    )


@router.post("/me/reply", response_model=PublicMessage, status_code=201)
async def reply_to_my_ticket(
    payload: ClientReply,
    ticket_id: uuid.UUID = Depends(current_client_ticket),
    session: AsyncSession = Depends(db_session),
) -> PublicMessage:
    ticket = await ticket_service.get_client_view(session, ticket_id)
    msg = await ticket_service.add_client_reply(session, ticket, payload.body)
    return PublicMessage.model_validate(msg)
