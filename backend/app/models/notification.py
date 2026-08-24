"""Notifications and per-channel delivery records."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import DeliveryStatus, NotificationChannel


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE")
    )
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    recipient_email: Mapped[str | None] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column()
    payload: Mapped[dict | None] = mapped_column(JSONB)


class NotificationDelivery(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notification_deliveries"
    notification_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        PGEnum(NotificationChannel, name="notification_channel",
               values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        PGEnum(DeliveryStatus, name="delivery_status",
               values_callable=lambda e: [x.value for x in e]),
        default=DeliveryStatus.PENDING, nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(500))
    provider_message_id: Mapped[str | None] = mapped_column(String(200))
