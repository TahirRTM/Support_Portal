"""OTP issuance/verification and scoped client-session issuance.

A client session is a JWT with kind="client" scoped to a single ticket_id. It
can never satisfy staff authorization (different kind + no permissions).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthError, RateLimitError, ValidationError
from app.models.security import ClientSession, OTPRecord
from app.models.ticket import Ticket
from app.security import otp as otp_lib
from app.security.jwt import create_token, decode_token
from app.security.tokens import generate_token, hash_token


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def issue_otp(session: AsyncSession, ticket: Ticket) -> str:
    """Create/replace the OTP for a ticket. Returns the raw code (for delivery).

    Raw code is NEVER persisted or logged; only its hash is stored.
    """
    s = get_settings()
    # Enforce resend cooldown against the latest active record.
    existing = (await session.execute(
        select(OTPRecord).where(OTPRecord.ticket_id == ticket.id)
        .order_by(OTPRecord.created_at.desc())
    )).scalars().first()
    if existing and existing.consumed_at is None:
        elapsed = (_now() - existing.last_sent_at).total_seconds()
        if elapsed < s.otp_resend_cooldown_seconds:
            raise RateLimitError(int(s.otp_resend_cooldown_seconds - elapsed),
                                 "Please wait before requesting another code.")
    code = otp_lib.generate_otp()
    record = OTPRecord(
        ticket_id=ticket.id,
        email=ticket.client_email,
        code_hash=otp_lib.hash_otp(code, ticket_id=str(ticket.id)),
        expires_at=_now() + timedelta(seconds=s.otp_ttl_seconds),
        max_attempts=s.otp_max_attempts,
        last_sent_at=_now(),
    )
    session.add(record)
    await session.commit()
    return code


async def verify_otp(
    session: AsyncSession, ticket: Ticket, code: str,
) -> str:
    """Verify OTP and issue a scoped client session token. Generic errors only."""
    record = (await session.execute(
        select(OTPRecord).where(OTPRecord.ticket_id == ticket.id)
        .order_by(OTPRecord.created_at.desc())
    )).scalars().first()
    if not record or record.consumed_at is not None:
        raise AuthError("Invalid or expired code.")
    if _now() > record.expires_at:
        raise AuthError("Invalid or expired code.")
    if record.attempts >= record.max_attempts:
        raise AuthError("Invalid or expired code.")
    record.attempts += 1
    if not otp_lib.verify_otp(code, ticket_id=str(ticket.id), stored_hash=record.code_hash):
        await session.commit()
        raise AuthError("Invalid or expired code.")
    record.consumed_at = _now()

    s = get_settings()
    raw = generate_token()
    cs = ClientSession(
        ticket_id=ticket.id, email=ticket.client_email,
        token_hash=hash_token(raw),
        expires_at=_now() + timedelta(seconds=s.client_session_ttl_seconds),
    )
    session.add(cs)
    await session.commit()
    # The JWT binds the session id + ticket scope; DB record allows revocation.
    return create_token(
        subject=str(cs.id), kind="client",
        ttl_seconds=s.client_session_ttl_seconds,
        claims={"ticket_id": str(ticket.id), "scope": "client_ticket"},
    )


async def resolve_client_session(
    session: AsyncSession, token: str,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Validate a client token server-side. Returns (session_id, ticket_id)."""
    payload = decode_token(token, expected_kind="client")
    if payload.get("scope") != "client_ticket":
        raise AuthError("Invalid session.")
    try:
        cs_id = uuid.UUID(payload["sub"])
        ticket_id = uuid.UUID(payload["ticket_id"])
    except (KeyError, ValueError):
        raise AuthError("Invalid session.")
    cs = (await session.execute(
        select(ClientSession).where(ClientSession.id == cs_id)
    )).scalar_one_or_none()
    if not cs or cs.revoked or cs.ticket_id != ticket_id:
        raise AuthError("Invalid session.")
    if _now() > cs.expires_at:
        raise AuthError("Session expired.")
    return cs_id, ticket_id
