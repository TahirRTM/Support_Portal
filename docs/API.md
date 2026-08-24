# API

Interactive OpenAPI at `/docs`; schema at `/api/v1/openapi.json`.
All responses use a consistent error envelope:
```json
{ "error": { "code": "rate_limited", "message": "...", "request_id": "..." } }
```

## Client (no admin JWT)
- `POST /api/v1/support/tickets` — create (rate limited 3/IP/5min, Turnstile)
- `POST /api/v1/support/tickets/otp` — request OTP (case_number + email)
- `POST /api/v1/support/tickets/otp/verify` — verify -> scoped client session
- `GET  /api/v1/support/tickets/me` — view scoped ticket (Bearer client token)
- `POST /api/v1/support/tickets/me/reply` — public client reply
- `GET  /api/v1/reference/categories|priorities`

## Staff auth
- `POST /api/v1/auth/login` `refresh` `logout` `logout-all`
- `GET  /api/v1/auth/me` `sessions` · `DELETE /auth/sessions/{id}`

## Admin tickets (permission-gated)
- `GET  /api/v1/admin/tickets` (q, status, overdue, unassigned, sort, page)
- `GET  /api/v1/admin/tickets/{id}` (staff sees internal notes)
- `POST /api/v1/admin/tickets/{id}/status|assign|fields|messages`

## Health
- `GET /api/v1/health/live|ready`
