"""JWT encode/decode with a strict algorithm allow-list and split secrets."""
from __future__ import annotations

import time
import uuid
from typing import Any, Literal

import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthError

TokenKind = Literal["access", "refresh", "client"]


def _secret(kind: TokenKind) -> str:
    s = get_settings()
    if kind == "refresh":
        return s.refresh_token_secret
    # access + client tokens are signed with the access secret but carry a
    # distinct "scope" claim so a client token can never be used as staff.
    return s.access_token_secret


def create_token(*, subject: str, kind: TokenKind, ttl_seconds: int,
                 claims: dict[str, Any] | None = None) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "nbf": now,
        "exp": now + ttl_seconds,
        "jti": uuid.uuid4().hex,
        "kind": kind,
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, _secret(kind), algorithm=get_settings().jwt_algorithm)


def decode_token(token: str, *, expected_kind: TokenKind) -> dict[str, Any]:
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            _secret(expected_kind),
            algorithms=[s.jwt_algorithm],  # strict allow-list, no "none"
            options={"require": ["exp", "iat", "sub", "kind"]},
        )
    except jwt.PyJWTError:
        raise AuthError("Invalid or expired token.")
    if payload.get("kind") != expected_kind:
        raise AuthError("Invalid token type.")
    return payload
