"""Deterministic fallback used when AI is disabled or fails.

Never raises. Guarantees the client always receives an acknowledgment and the
ticket always gets *some* classification, keeping AI strictly non-blocking.
"""
from __future__ import annotations

from app.providers.ai.base import AIProvider, AIResult, TicketContext

FALLBACK_ACK = (
    "Your support request has been received. "
    "Our support team will review it shortly."
)

_URGENT_HINTS = ("urgent", "asap", "down", "outage", "cannot", "can't", "critical", "payment")


class FallbackAIProvider(AIProvider):
    name = "fallback"

    async def analyze(self, ctx: TicketContext) -> AIResult:
        text = f"{ctx.subject} {ctx.description}".lower()
        priority = None
        if ctx.known_priorities:
            urgent = any(h in text for h in _URGENT_HINTS)
            # Pick the most/least urgent by naming convention if available.
            priority = _match(ctx.known_priorities, "high" if urgent else "medium")
        summary = ctx.subject.strip()[:280] or "Support request"
        return AIResult(
            summary=summary,
            suggested_category=(ctx.known_categories[0] if ctx.known_categories else None),
            suggested_priority=priority,
            acknowledgment=FALLBACK_ACK,
            confidence=0.0,
            used_fallback=True,
            provider=self.name,
        )


def _match(options: list[str], needle: str) -> str | None:
    for o in options:
        if needle in o.lower():
            return o
    return options[0] if options else None
