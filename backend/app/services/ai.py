"""AI orchestration. Always non-blocking; always yields an acknowledgment.

Called from a Celery task AFTER the ticket is committed. On any failure it falls
back to the deterministic provider so ticket creation is never impacted.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.ai import AIAcknowledgment, AIAnalysis
from app.models.reference import Category, Department, Priority
from app.models.ticket import Ticket
from app.providers.ai import get_ai_provider
from app.providers.ai.base import TicketContext
from app.providers.ai.fallback import FALLBACK_ACK, FallbackAIProvider

log = get_logger(__name__)


async def analyze_ticket(session: AsyncSession, ticket_id: uuid.UUID) -> AIAnalysis:
    ticket = (await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )).scalar_one_or_none()
    if not ticket:
        raise ValueError("ticket not found")

    cats = [c.name for c in (await session.execute(select(Category))).scalars()]
    prios = [p.name for p in (await session.execute(select(Priority))).scalars()]
    deps = [d.name for d in (await session.execute(select(Department))).scalars()]

    ctx = TicketContext(
        case_number=ticket.case_number, subject=ticket.subject,
        description=ticket.description, known_categories=cats,
        known_priorities=prios, known_departments=deps,
    )
    provider = get_ai_provider()
    try:
        result = await provider.analyze(ctx)
    except Exception as exc:
        log.warning("ai_provider_failed_using_fallback", error=str(exc))
        result = await FallbackAIProvider().analyze(ctx)

    analysis = AIAnalysis(
        ticket_id=ticket.id, provider=result.provider, model=result.model,
        summary=result.summary, suggested_category=result.suggested_category,
        suggested_priority=result.suggested_priority,
        suggested_department=result.suggested_department,
        sentiment=result.sentiment, suggested_response=result.suggested_response,
        confidence=result.confidence, used_fallback=result.used_fallback,
    )
    session.add(analysis)
    ack_text = result.acknowledgment or FALLBACK_ACK
    session.add(AIAcknowledgment(
        ticket_id=ticket.id, message=ack_text,
        used_fallback=result.used_fallback or result.acknowledgment is None,
    ))
    await session.commit()
    await session.refresh(analysis)
    return analysis
