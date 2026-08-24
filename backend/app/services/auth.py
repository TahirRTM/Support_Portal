"""Staff authentication: login, refresh rotation, reuse detection, lockout.

Refresh tokens are opaque random strings stored hashed, grouped by a family_id.
Rotation issues a new token and marks the old used. If an already-used (or
revoked) token is presented again, the entire family is revoked (reuse
detection).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthError
from app.models.user import RefreshToken, User
from app.security.jwt import create_token
from app.security.passwords import needs_rehash, hash_password, verify_password
from app.security.tokens import generate_token, hash_token

MAX_FAILED = 5
LOCK_MINUTES = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = (await session.execute(
        select(User).where(User.email == email.lower(), User.deleted_at.is_(None))
    )).scalar_one_or_none()
    # Timing-equalized verification even when the user is missing.
    ok = verify_password(password, user.password_hash if user else None)
    if user and user.locked_until and user.locked_until > _now():
        raise AuthError("Authentication failed.")
    if not user or not ok or not user.is_active:
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED:
                user.locked_until = _now() + timedelta(minutes=LOCK_MINUTES)
            await session.commit()
        raise AuthError("Authentication failed.")
    user.failed_login_count = 0
    user.locked_until = None
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    await session.commit()
    return user


async def issue_tokens(
    session: AsyncSession, user: User, *, family_id: uuid.UUID | None = None,
    user_agent: str | None = None, ip: str | None = None,
) -> tuple[str, str]:
    s = get_settings()
    access = create_token(subject=str(user.id), kind="access",
                          ttl_seconds=s.access_token_ttl_seconds,
                          claims={"email": user.email})
    raw_refresh = generate_token()
    fam = family_id or uuid.uuid4()
    session.add(RefreshToken(
        user_id=user.id, family_id=fam, token_hash=hash_token(raw_refresh),
        expires_at=_now() + timedelta(seconds=s.refresh_token_ttl_seconds),
        user_agent=user_agent, ip=ip,
    ))
    await session.commit()
    return access, raw_refresh


async def rotate_refresh(
    session: AsyncSession, raw_refresh: str, *, user_agent: str | None = None,
    ip: str | None = None,
) -> tuple[str, str]:
    token = (await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )).scalar_one_or_none()
    if not token:
        raise AuthError("Invalid refresh token.")
    if token.revoked or token.used_at is not None:
        # Reuse detected: nuke the whole family.
        await session.execute(
            update(RefreshToken).where(RefreshToken.family_id == token.family_id)
            .values(revoked=True)
        )
        await session.commit()
        raise AuthError("Refresh token reuse detected.")
    if token.expires_at < _now():
        raise AuthError("Refresh token expired.")
    user = (await session.execute(
        select(User).where(User.id == token.user_id, User.is_active.is_(True))
    )).scalar_one_or_none()
    if not user:
        raise AuthError("Invalid refresh token.")
    token.used_at = _now()
    access, new_refresh = await issue_tokens(
        session, user, family_id=token.family_id, user_agent=user_agent, ip=ip)
    token.replaced_by = (await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(new_refresh))
    )).scalar_one().id
    await session.commit()
    return access, new_refresh


async def revoke_refresh(session: AsyncSession, raw_refresh: str) -> None:
    token = (await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh))
    )).scalar_one_or_none()
    if token:
        token.revoked = True
        await session.commit()


async def revoke_all(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id)
        .values(revoked=True)
    )
    await session.commit()
