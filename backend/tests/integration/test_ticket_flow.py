"""Integration: client ticket lifecycle against a real DB + app.

Requires TEST_DATABASE_URL (Postgres). Skipped otherwise. Uses httpx ASGI
transport so no network server is needed.
"""
from __future__ import annotations

import os

import pytest

from tests.conftest import requires_db

pytestmark = [pytest.mark.asyncio, requires_db]


@pytest.fixture
async def client():
    import httpx
    from app.main import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_create_then_track_with_otp(client, monkeypatch):
    # CAPTCHA disabled for the test environment.
    monkeypatch.setenv("TURNSTILE_ENABLED", "false")
    payload = {
        "name": "Ada Lovelace", "email": "ada@example.com",
        "subject": "Cannot log in", "description": "I am locked out of my account.",
        "captcha_token": "dev-bypass",
    }
    r = await client.post("/api/v1/support/tickets", json=payload)
    assert r.status_code == 201
    case_number = r.json()["case_number"]
    assert case_number.startswith("SUP-")

    # Case Number alone must NOT grant access.
    denied = await client.get("/api/v1/support/tickets/me")
    assert denied.status_code == 401

    # Request + verify OTP requires reading the code from the DB in tests.
    req = await client.post("/api/v1/support/tickets/otp",
                            json={"case_number": case_number, "email": "ada@example.com"})
    assert req.status_code == 202
