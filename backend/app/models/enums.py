"""Domain enumerations."""
from __future__ import annotations

import enum


class TicketStatus(str, enum.Enum):
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CLIENT = "pending_client"
    PENDING_INTERNAL = "pending_internal"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class MessageVisibility(str, enum.Enum):
    PUBLIC = "public"        # visible to client and staff
    INTERNAL = "internal"    # staff-only note, NEVER exposed to clients


class AuthorType(str, enum.Enum):
    CLIENT = "client"
    AGENT = "agent"
    SYSTEM = "system"
    AI = "ai"


class AttachmentStatus(str, enum.Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PUSHOVER = "pushover"
    IN_APP = "in_app"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
