"""Reference data: categories, priorities, departments, teams."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Department(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "departments"
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))


class SupportTeam(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "support_teams"
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )


class Category(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "categories"
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    default_department_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )


class Priority(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "priorities"
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    # Lower rank = more urgent. Used by SLA + assignment engines.
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    sla_response_minutes: Mapped[int | None] = mapped_column(Integer)
    sla_resolution_minutes: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("rank", name="uq_priority_rank"),)
