"""Celery application + beat schedule.

Redis is the broker/backend. Tasks run outside the request/response cycle so
external notifications and AI never block or roll back ticket creation.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "ai_support_portal",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "sla-sweep": {
            "task": "app.workers.tasks.sweep_sla",
            "schedule": 60.0,  # every minute
        },
        "notification-retry-sweep": {
            "task": "app.workers.tasks.retry_failed_notifications",
            "schedule": 120.0,
        },
    },
)
