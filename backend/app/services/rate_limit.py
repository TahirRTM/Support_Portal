"""Fixed-window rate limiting backed by Redis atomic INCR + EXPIRE.

Business rule: max N new-ticket creations per client IP per window.
Returns the current count and remaining TTL so callers can set Retry-After.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.redis import RedisLike, get_redis


@dataclass(slots=True)
class RateResult:
    allowed: bool
    count: int
    limit: int
    retry_after: int


async def _hit(redis: RedisLike, key: str, limit: int, window: int) -> RateResult:
    count = await redis.incr(key)
    if count == 1:
        # First hit in this window starts the TTL clock atomically-enough:
        # INCR then EXPIRE only on the fresh key.
        await redis.expire(key, window)
    ttl = await redis.ttl(key)
    if ttl < 0:
        # Safety: ensure a window is always set.
        await redis.expire(key, window)
        ttl = window
    return RateResult(allowed=count <= limit, count=count, limit=limit, retry_after=ttl)


async def check_ticket_creation(ip: str) -> RateResult:
    s = get_settings()
    key = f"rl:ticket_create:{ip}"
    return await _hit(get_redis(), key, s.ticket_create_limit, s.ticket_create_window_seconds)


async def check_otp_request(ticket_id: str, ip: str) -> RateResult:
    # Independent abuse guard for OTP requests (10 / 10 min per ticket+ip).
    key = f"rl:otp_req:{ticket_id}:{ip}"
    return await _hit(get_redis(), key, 10, 600)
