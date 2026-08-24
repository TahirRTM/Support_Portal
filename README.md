# AI Support Portal

Enterprise support-ticket platform: public client portal + admin/support console.
FastAPI + PostgreSQL + Redis + Celery backend, Next.js/TypeScript frontend,
Nginx, ClamAV, Docker.

## Highlights
- Secure Case Numbers; **Case Number alone never grants access**.
- Client access = Case Number + Email -> OTP -> short-lived scoped session.
- Internal notes are structurally impossible for clients to read.
- 3 new tickets / IP / 5 min (Redis), trusted-proxy IP resolution, Turnstile CAPTCHA.
- AI and external notifications are async; they never block or roll back ticket creation.
- Provider abstractions for AI, Email, WhatsApp, Pushover, and storage.

## Quick start (with Docker)
```bash
cp .env.example .env            # then set strong secrets
docker compose up --build
docker compose exec api alembic upgrade head
ADMIN_BOOTSTRAP_PASSWORD=... docker compose exec api python -m app.seed
```
API docs: http://localhost:8080/docs · Frontend: http://localhost:3000

## Layout
- `backend/` FastAPI app, models, services, providers, workers, migrations, tests
- `frontend/` Next.js client + admin UI
- `nginx/` reverse proxy config · `docs/` architecture/security/deployment/testing

See `PROGRESS.md` for exact status and `docs/TESTING.md` for what has/hasn't run.
