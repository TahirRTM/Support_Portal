"""Notification provider abstraction shared by all channels."""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(slots=True)
class NotificationMessage:
    to: str
    subject: str
    body: str
    metadata: dict | None = None


@dataclass(slots=True)
class SendResult:
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None


class NotificationProvider(abc.ABC):
    channel: str = "base"

    @abc.abstractmethod
    async def send(self, msg: NotificationMessage) -> SendResult:
        ...
