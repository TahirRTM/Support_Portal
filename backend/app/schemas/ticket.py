from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MessageVisibility, TicketStatus


class TicketCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    subject: str = Field(min_length=3, max_length=300)
    description: str = Field(min_length=3, max_length=20000)
    category_id: uuid.UUID | None = None
    priority_id: uuid.UUID | None = None
    captcha_token: str | None = None


class TicketCreated(BaseModel):
    case_number: str
    status: TicketStatus
    created_at: datetime
    message: str = "Support Request Received"
    acknowledgment: str | None = None


class PublicMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_type: str
    author_display: str
    body: str
    created_at: datetime


class StatusEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: str | None
    to_status: str
    created_at: datetime
    note: str | None


class PublicAttachment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    original_filename: str
    content_type: str
    size_bytes: int


class ClientTicketView(BaseModel):
    """Client-facing ticket. Internal notes are structurally excluded."""
    case_number: str
    subject: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    messages: list[PublicMessage]
    attachments: list[PublicAttachment]
    timeline: list[StatusEvent]


class ClientReply(BaseModel):
    body: str = Field(min_length=1, max_length=20000)
