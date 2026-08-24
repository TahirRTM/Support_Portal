import pytest
from app.core.redis import InMemoryRedis, set_redis
from app.services.rate_limit import check_ticket_creation


@pytest.mark.asyncio
async def test_three_allowed_fourth_blocked():
    set_redis(InMemoryRedis())
    ip = "203.0.113.5"
    r1 = await check_ticket_creation(ip)
    r2 = await check_ticket_creation(ip)
    r3 = await check_ticket_creation(ip)
    r4 = await check_ticket_creation(ip)
    assert (r1.allowed, r2.allowed, r3.allowed) == (True, True, True)
    assert r4.allowed is False
    assert r4.retry_after > 0
