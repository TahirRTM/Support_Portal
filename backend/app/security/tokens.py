"""Opaque secret tokens + SHA-256 hashing for at-rest storage.

Used for refresh tokens, client-session tokens, OTP transport tokens, and
password-reset tokens. Only the hash is stored; the raw value is returned once.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
