"""Core ticket aggregate: ticket, messages, attachments, status history."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import (
    AttachmentStatus,
    AuthorType,
    MessageVisibility,
    TicketStatus,
)


class Ticket(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tickets"

    # Public, opaque identifier shown to clients. Never exposes the DB id.
    case_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    # Contact info (client is not a platform user).
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_email: Mapped[str] = mapped_column(String(320), nullable=False)
    client_company: Mapped[str | None] = mapped_column(String(200))
    client_phone: Mapped[str | None] = mapped_column(String(40))

    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        PGEnum(TicketStatus, name="ticket_status", values_callable=lambda e: [x.value for x in e]),
        default=TicketStatus.NEW,
        nullable=False,
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL")
    )
    priority_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("priorities.id", ondelete="SET NULL")
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("support_teams.id", ondelete="SET NULL")
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    # SLA tracking
    sla_response_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_resolution_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sla_response_breached: Mapped[bool] = mapped_column(default=False, nullable=False)
    sla_resolution_breached: Mapped[bool] = mapped_column(default=False, nullable=False)

    source_ip: Mapped[str | None] = mapped_column(INET)

    messages: Mapped[list["TicketMessage"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["TicketStatusEvent"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_priority", "priority_id"),
        Index("ix_tickets_category", "category_id"),
        Index("ix_tickets_department", "department_id"),
        Index("ix_tickets_assigned_agent", "assigned_agent_id"),
        Index("ix_tickets_created_at", "created_at"),
        Index("ix_tickets_client_email", "client_email"),
        Index("ix_tickets_sla_resolution_due", "sla_resolution_due_at"),
    )


class TicketMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    author_type: Mapped[AuthorType] = mapped_column(
        PGEnum(AuthorType, name="author_type", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    author_display: Mapped[str] = mapped_column(String(200), nullable=False)

    # The single most security-critical flag in the system.
    visibility: Mapped[MessageVisibility] = mapped_column(
        PGEnum(MessageVisibility, name="message_visibility",
               values_callable=lambda e: [x.value for x in e]),
        default=MessageVisibility.PUBLIC,
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_ticket_messages_ticket_visibility", "ticket_id", "visibility"),
    )


class TicketAttachment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ticket_attachments"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ticket_messages.id", ondelete="CASCADE")
    )
    original_filename: Mapped[str] = mapped_column(String(400), nullable=False)
    content_type: Mapped[str] = mapped_column(String(200), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Storage key is opaque; physical paths are never exposed to clients.
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[AttachmentStatus] = mapped_column(
        PGEnum(AttachmentStatus, name="attachment_status",
               values_callable=lambda e: [x.value for x in e]),
        default=AttachmentStatus.PENDING,
        nullable=False,
    )
    scan_result: Mapped[str | None] = mapped_column(String(300))
    visibility: Mapped[MessageVisibility] = mapped_column(
        PGEnum(MessageVisibility, name="message_visibility", create_type=False,
               values_callable=lambda e: [x.value for x in e]),
        default=MessageVisibility.PUBLIC,
        nullable=False,
    )

    ticket: Mapped[Ticket] = relationship(back_populates="attachments")

    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_attachment_size_nonneg"),
        Index("ix_ticket_attachments_ticket", "ticket_id"),
    )


class TicketStatusEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ticket_status_history"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(String(500))

    ticket: Mapped[Ticket] = relationship(back_populates="status_history")

    __table_args__ = (
        Index("ix_ticket_status_history_ticket", "ticket_id", "created_at"),
    )
