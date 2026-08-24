# Operations

## Services
api (FastAPI), worker (Celery), beat (Celery Beat), db (Postgres), redis,
clamav, frontend (Next.js), nginx.

## Logs
Structured JSON via structlog; every request carries an `x-request-id` echoed in
responses and error envelopes. Aggregate by request_id when debugging.

## Queues
Celery uses Redis. Beat schedules the SLA sweep (60s) and notification retry
sweep (120s). Failed notification deliveries move pending->retrying->failed with
bounded attempts.

## Scaling
Api and worker are stateless; scale horizontally. Redis rate limiting is shared
across instances (do not use the in-memory fallback in production).
