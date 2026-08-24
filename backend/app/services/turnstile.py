"""Server-side Cloudflare Turnstile verification.

Client-side success is never trusted. Fails closed unless explicitly disabled
or a configured dev-bypass token is presented in non-production.
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.exceptions import CaptchaError
from app.core.logging import get_logger

log = get_logger(__name__)


async def verify_turnstile(token: str | None, *, remote_ip: str | None = None) -> None:
    s = get_settings()
    if not s.turnstile_enabled:
        return
    # Dev/testing bypass, only outside production and only for the exact token.
    if not s.is_production and token == s.turnstile_dev_bypass_token:
        return
    if not token:
        raise CaptchaError("CAPTCHA token missing.")
    if not s.turnstile_secret_key:
        # Misconfiguration must fail closed, never open.
        log.error("turnstile_secret_missing")
        raise CaptchaError("CAPTCHA is not configured.")
    data = {"secret": s.turnstile_secret_key, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(s.turnstile_verify_url, data=data)
            body = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("turnstile_verify_error", error=str(exc))
        raise CaptchaError("CAPTCHA verification unavailable.")
    if not body.get("success"):
        raise CaptchaError()
