"""Redis accessor with a safe in-memory fallback for dev/test.

The fallback implements just enough of the async Redis surface used by the rate
limiter and OTP abuse guards so the app runs without a Redis server present.
Production always uses the real client.
"""
from __future__ import annotations

import time
from typing import Protocol

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class RedisLike(Protocol):
    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, seconds: int) -> bool: ...
    async def ttl(self, key: str) -> int: ...
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ex: int | None = None) -> bool: ...
    async def delete(self, key: str) -> int: ...


class InMemoryRedis:
    """Process-local stand-in. NOT for multi-process production use."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    def _expired(self, key: str) -> bool:
        v = self._store.get(key)
        if v and v[1] is not None and v[1] < time.time():
            self._store.pop(key, None)
            return True
        return False

    async def incr(self, key: str) -> int:
        self._expired(key)
        cur = int(self._store.get(key, ("0", None))[0]) + 1
        exp = self._store.get(key, (None, None))[1]
        self._store[key] = (str(cur), exp)
        return cur

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._store:
            val = self._store[key][0]
            self._store[key] = (val, time.time() + seconds)
            return True
        return False

    async def ttl(self, key: str) -> int:
        v = self._store.get(key)
        if not v or v[1] is None:
            return -1
        return max(0, int(v[1] - time.time()))

    async def get(self, key: str) -> str | None:
        if self._expired(key):
            return None
        v = self._store.get(key)
        return v[0] if v else None

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._store[key] = (value, time.time() + ex if ex else None)
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0


_client: RedisLike | None = None


def get_redis() -> RedisLike:
    global _client
    if _client is not None:
        return _client
    try:
        import redis.asyncio as aioredis  # type: ignore

        _client = aioredis.from_url(
            get_settings().redis_url, encoding="utf-8", decode_responses=True
        )
        log.info("redis_client_initialized")
    except Exception as exc:  # pragma: no cover - depends on env
        log.warning("redis_unavailable_using_memory_fallback", error=str(exc))
        _client = InMemoryRedis()
    return _client


def set_redis(client: RedisLike) -> None:
    """Test hook to inject a client."""
    global _client
    _client = client
