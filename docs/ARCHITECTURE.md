# Architecture

## Layers
- **API (app/api/v1)**: thin HTTP handlers, validation, auth dependencies.
- **Services (app/services)**: business logic (tickets, auth, OTP/session, SLA,
  assignment, notifications, AI, attachments, rate limiting).
- **Providers (app/providers)**: swappable integrations (AI, notifications, storage).
- **Models (app/models)**: SQLAlchemy 2.x async ORM, UUID PKs, tz-aware timestamps.
- **Workers (app/workers)**: Celery tasks + beat schedule (AI, notifications, SLA sweep).

## Critical workflow — ticket creation
1. Resolve client IP (trusted-proxy aware) and enforce the Redis rate limit.
2. Verify Turnstile server-side (fails closed).
3. Create + **commit** the ticket (the only critical transaction).
4. Post-commit: routing + SLA due dates.
5. Persist notification records, then **enqueue** async dispatch.
6. **Enqueue** async AI analysis + acknowledgment.
Steps 4-6 can fail without affecting the committed ticket.

## Client access model
Case Number + Email -> OTP (hashed, TTL, attempt-capped) -> JWT `kind=client`
scoped to one `ticket_id`, backed by a revocable `client_sessions` row. This
token cannot satisfy staff authorization (different kind, no permissions).

## Data integrity
Enums stored as PG enums; indexes on case_number, status, priority, category,
department, assignment, timestamps, client_email, SLA due dates; check + unique
constraints; soft delete on tickets/users.
