# Deployment

## Prerequisites
Docker + Docker Compose, a domain, TLS certificates.

## Steps
1. `cp .env.example .env`; set strong `ACCESS_TOKEN_SECRET` and
   `REFRESH_TOKEN_SECRET` (>=32 chars, distinct), DB/Redis URLs, provider keys.
   Production refuses to boot with weak/placeholder/identical secrets.
2. Build + start: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
3. Migrate: `docker compose exec api alembic upgrade head`
4. Seed: `ADMIN_BOOTSTRAP_PASSWORD=... docker compose exec api python -m app.seed`
5. TLS: place certs in `nginx/certs/` and enable the 443 server block.

## Health
- Liveness: `/api/v1/health/live` · Readiness: `/api/v1/health/ready`
- Nginx sets `client_max_body_size 15m`; keep in sync with `MAX_REQUEST_BODY_BYTES`.

## Rollback
Images are tagged per release; redeploy the previous tag and run
`alembic downgrade -1` only if the release included a migration.

## Backups
`scripts/backup.sh` (pg_dump -Fc) and `scripts/restore.sh` (pg_restore). Schedule
backup.sh via cron/systemd timer; test restores regularly.
