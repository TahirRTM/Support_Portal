"""FastAPI dependencies: DB session, client session, staff auth, permissions."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import AuthError, ForbiddenError
from app.services.client_session import resolve_client_session


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for s in get_session():
        yield s


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Missing bearer token.")
    return authorization.split(" ", 1)[1].strip()


async def current_client_ticket(
    request: Request,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session),
) -> uuid.UUID:
    """Resolve the scoped client session and return the ticket_id it may access.

    This is the ONLY gate for client ticket access. Case Number alone is never
    sufficient; a valid, unexpired, unrevoked client session is required.
    """
    token = _bearer(authorization)
    _, ticket_id = await resolve_client_session(session, token)
    return ticket_id


async def current_staff(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(db_session),
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.user import Role, User
    from app.security.jwt import decode_token

    token = _bearer(authorization)
    payload = decode_token(token, expected_kind="access")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise AuthError("Invalid token.")
    user = (await session.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True),
                          User.deleted_at.is_(None))
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )).scalar_one_or_none()
    if not user:
        raise AuthError("Invalid token.")
    return user


def require_permission(code: str):
    async def _dep(user=Depends(current_staff)):
        perms = user.permission_codes
        if "*" not in perms and code not in perms:
            raise ForbiddenError(f"Missing permission: {code}")
        return user
    return _dep
