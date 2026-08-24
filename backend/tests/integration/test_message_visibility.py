"""Integration: internal notes must never appear in the client view."""
from __future__ import annotations

import pytest

from tests.conftest import requires_db

pytestmark = [pytest.mark.asyncio, requires_db]


async def test_internal_note_excluded_from_client_view():
    from app.models.enums import MessageVisibility
    from app.models.ticket import Ticket, TicketMessage
    from app.services.tickets import public_messages

    t = Ticket(case_number="SUP-2026-TESTTEST01", client_name="X",
               client_email="x@example.com", subject="s", description="d")
    t.messages = [
        TicketMessage(author_type="agent", author_display="A",
                      visibility=MessageVisibility.PUBLIC, body="public"),
        TicketMessage(author_type="agent", author_display="A",
                      visibility=MessageVisibility.INTERNAL, body="SECRET NOTE"),
    ]
    visible = public_messages(t)
    assert all(m.visibility == MessageVisibility.PUBLIC for m in visible)
    assert "SECRET NOTE" not in [m.body for m in visible]
