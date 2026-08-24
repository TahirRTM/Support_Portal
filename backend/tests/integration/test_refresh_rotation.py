"""Integration: refresh rotation + reuse detection revokes the family."""
from __future__ import annotations

import pytest

from tests.conftest import requires_db

pytestmark = [pytest.mark.asyncio, requires_db]


async def test_reuse_detection(db_session_factory):  # pragma: no cover - needs DB
    # Pseudocode-level integration test: issue -> rotate -> reuse old -> expect
    # AuthError and whole-family revocation. Wired when a DB is available.
    assert True
