"""Cryptographically secure OTP generation and hashing."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from app.core.config import get_settings


def generate_otp() -> str:
    length = get_settings().otp_length
    upper = 10 ** length
    # Uniform, unbiased selection in [0, 10**length).
    return str(secrets.randbelow(upper)).zfill(length)


def hash_otp(code: str, *, ticket_id: str) -> str:
    # Bind the hash to the ticket so a leaked hash cannot be replayed elsewhere.
    secret = get_settings().access_token_secret.encode()
    msg = f"{ticket_id}:{code}".encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def verify_otp(code: str, *, ticket_id: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(code, ticket_id=ticket_id), stored_hash)
