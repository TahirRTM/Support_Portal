"""Stored AI analyses and acknowledgments."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AIAnalysis(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_analyses"
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text)
    suggested_category: Mapped[str | None] = mapped_column(String(120))
    suggested_priority: Mapped[str | None] = mapped_column(String(60))
    suggested_department: Mapped[str | None] = mapped_column(String(120))
    sentiment: Mapped[str | None] = mapped_column(String(40))
    suggested_response: Mapped[str | None] = mapped_column(Text)
    kb_suggestions: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    used_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)


class AIAcknowledgment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_acknowledgments"
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    used_fallback: Mapped[bool] = mapped_column(default=False, nullable=False)
