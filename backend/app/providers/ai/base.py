"""AI provider abstraction.

All providers return a normalized AIResult. Ticket content is untrusted and is
wrapped/isolated before being sent, and providers must never let ticket text
override system policy (prompt-injection resistance is applied in the service).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass(slots=True)
class TicketContext:
    case_number: str
    subject: str
    description: str
    known_categories: list[str] = field(default_factory=list)
    known_priorities: list[str] = field(default_factory=list)
    known_departments: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AIResult:
    summary: str | None = None
    suggested_category: str | None = None
    suggested_priority: str | None = None
    suggested_department: str | None = None
    sentiment: str | None = None
    suggested_response: str | None = None
    acknowledgment: str | None = None
    confidence: float | None = None
    used_fallback: bool = False
    provider: str = "unknown"
    model: str | None = None


class AIProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def analyze(self, ctx: TicketContext) -> AIResult:
        ...
