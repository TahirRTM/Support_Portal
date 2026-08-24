from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageVisibility, TicketStatus


class AdminTicketRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_number: str
    subject: str
    status: TicketStatus
    client_name: str
    client_email: str
    created_at: datetime
    updated_at: datetime
    sla_response_breached: bool
    sla_resolution_breached: bool
    assigned_agent_id: uuid.UUID | None


class AdminMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_type: str
    author_display: str
    visibility: MessageVisibility
    body: str
    created_at: datetime


class AdminTicketDetail(AdminTicketRow):
    description: str
    client_company: str | None
    client_phone: str | None
    department_id: uuid.UUID | None
    team_id: uuid.UUID | None
    category_id: uuid.UUID | None
    priority_id: uuid.UUID | None
    sla_response_due_at: datetime | None
    sla_resolution_due_at: datetime | None
    messages: list[AdminMessage]


class StatusChange(BaseModel):
    status: TicketStatus
    note: str | None = Field(default=None, max_length=500)


class AssignChange(BaseModel):
    agent_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None


class FieldChange(BaseModel):
    category_id: uuid.UUID | None = None
    priority_id: uuid.UUID | None = None


class StaffMessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=20000)
    internal: bool = False  # True => internal note (never visible to clients)
