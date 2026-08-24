"""Liveness / readiness / health endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict:
    return {"status": "alive"}


@router.get("/health/ready")
async def ready() -> dict:
    checks = {"database": False, "redis": False}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        await get_redis().set("health:ping", "1", ex=5)
        checks["redis"] = True
    except Exception:
        checks["redis"] = False
    status = "ready" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
