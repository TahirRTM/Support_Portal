"""Staff auth endpoints. Refresh token lives in an HttpOnly, Secure cookie."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthError
from app.core.ip import resolve_client_ip
from app.dependencies import current_staff, db_session
from app.models.user import RefreshToken
from app.schemas.auth import LoginRequest, MeResponse, SessionInfo, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, raw: str) -> None:
    s = get_settings()
    response.set_cookie(
        REFRESH_COOKIE, raw, httponly=True, secure=s.is_production,
        samesite="strict", max_age=s.refresh_token_ttl_seconds, path="/api/v1/auth",
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response,
                session: AsyncSession = Depends(db_session)) -> TokenResponse:
    user = await auth_service.authenticate(session, str(payload.email), payload.password)
    access, refresh = await auth_service.issue_tokens(
        session, user, user_agent=request.headers.get("user-agent"),
        ip=resolve_client_ip(request),
    )
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access,
                         expires_in=get_settings().access_token_ttl_seconds)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response,
                  session: AsyncSession = Depends(db_session)) -> TokenResponse:
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise AuthError("Missing refresh token.")
    access, new_refresh = await auth_service.rotate_refresh(
        session, raw, user_agent=request.headers.get("user-agent"),
        ip=resolve_client_ip(request),
    )
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=access,
                         expires_in=get_settings().access_token_ttl_seconds)


@router.post("/logout")
async def logout(request: Request, response: Response,
                 session: AsyncSession = Depends(db_session)) -> dict:
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        await auth_service.revoke_refresh(session, raw)
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return {"status": "logged_out"}


@router.post("/logout-all")
async def logout_all(response: Response, user=Depends(current_staff),
                     session: AsyncSession = Depends(db_session)) -> dict:
    await auth_service.revoke_all(session, user.id)
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return {"status": "all_sessions_revoked"}


@router.get("/me", response_model=MeResponse)
async def me(user=Depends(current_staff)) -> MeResponse:
    return MeResponse(id=user.id, email=user.email, full_name=user.full_name,
                      permissions=sorted(user.permission_codes))


@router.get("/sessions", response_model=list[SessionInfo])
async def sessions(user=Depends(current_staff),
                   session: AsyncSession = Depends(db_session)) -> list[SessionInfo]:
    rows = (await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
        .order_by(RefreshToken.created_at.desc())
    )).scalars().all()
    return [SessionInfo.model_validate(r) for r in rows]


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: uuid.UUID, user=Depends(current_staff),
                         session: AsyncSession = Depends(db_session)) -> dict:
    row = (await session.execute(
        select(RefreshToken).where(RefreshToken.id == session_id,
                                   RefreshToken.user_id == user.id)
    )).scalar_one_or_none()
    if not row:
        raise AuthError("Session not found.")
    row.revoked = True
    await session.commit()
    return {"status": "revoked"}
