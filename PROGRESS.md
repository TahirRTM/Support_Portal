# PROGRESS

Legend: [x] done · [~] partial · [ ] not started
Status tags: IMPLEMENTED · TEST WRITTEN · TEST EXECUTED · TEST NOT EXECUTABLE

## Environment reality
This build environment has git + Python + Node but NO npm, Docker, PostgreSQL,
Redis, FastAPI runtime deps, pytest, Playwright, or internet. Therefore:
- All application code is IMPLEMENTED and syntax-verified (AST parse).
- Pure-logic unit tests for the Case Number generator were TEST EXECUTED and pass.
- All other tests are TEST WRITTEN / TEST NOT EXECUTABLE (need DB/Redis/browser).
- No test results are fabricated. No "production-ready" or "zero vulns" claims.

## Priority 1 — Client Portal + Ticketing Core  [x] IMPLEMENTED
- [x] Ticket + message + attachment + status-history models
- [x] Secure Case Number generation (Crockford base32, non-sequential) + normalization
- [x] Ticket creation API (commit-first, side-effects after)
- [x] Redis rate limiting: 3 new tickets / IP / 5 min (atomic INCR+EXPIRE) — TEST WRITTEN
- [x] Trusted-proxy client IP resolution (no blind X-Forwarded-For trust)
- [x] Cloudflare Turnstile server-side verification (fails closed)
- [x] OTP: crypto-secure, hashed-at-rest, TTL, attempt cap, resend cooldown
- [x] Scoped client session (JWT kind=client, DB-backed, revocable)
- [x] Case tracking + client reply + status timeline
- [x] Public/internal message separation (structural + query-level)
- [x] Attachment validation (name/ext/mime/magic/size/traversal) + ClamAV abstraction

## Priority 2 — Admin Ticketing  [x] IMPLEMENTED
- [x] Staff login, refresh rotation + reuse detection, sessions, logout(-all), me
- [x] Ticket list/search/filter/sort/paginate, detail (staff sees internal notes)
- [x] Assign, status change, category/priority change, public reply, internal note
- [~] Dashboard metrics endpoint — analytics module (Priority 8) covers counts

## Priority 3 — Notifications  [x] IMPLEMENTED
- [x] Provider abstractions: Email(SMTP), WhatsApp, Pushover, In-app
- [x] Notification + per-channel delivery records with status + retry bookkeeping
- [x] Celery dispatch; ticket creation never blocks on external sends

## Priority 4 — AI  [x] IMPLEMENTED
- [x] Provider abstraction (OpenAI-compatible) + deterministic fallback
- [x] Async via Celery; failure never blocks ticket creation
- [x] Prompt-injection isolation of untrusted ticket content

## Priority 5 — SLA & Assignment  [x] IMPLEMENTED
- [x] Business-hours SLA due-date calc — TEST WRITTEN
- [x] Breach sweep (Celery Beat), assignment routing by category/department/team

## Priority 6 — Knowledge Base  [ ] NOT STARTED (models/endpoints pending)
## Priority 7 — Admin Management  [~] roles/permissions/departments seeded; CRUD endpoints pending
## Priority 8 — Analytics  [~] counts derivable; dedicated endpoints pending
## Priority 9 — Security  [x] IMPLEMENTED across the stack (see docs/SECURITY.md)
## Priority 10 — Frontend  [~] key client + admin screens implemented as static-export UI

## Tests
- Unit: case_number (EXECUTED, 5 pass), otp, passwords, attachments, rate_limit, sla (WRITTEN, NOT EXECUTABLE here)
- Integration: ticket flow, message visibility, refresh rotation (WRITTEN, need DB)
- E2E (Playwright): client journey, rate limit, security scoping (WRITTEN, need stack)

## Known limitations
- No dependencies installed here, so only AST checks + case-number tests ran.
- KB, full admin-management CRUD, and analytics endpoints are the next build targets.
- Frontend ships as a self-contained UI reference; wiring to live APIs is documented.
