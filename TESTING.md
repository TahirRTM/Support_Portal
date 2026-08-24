# Testing

## What ran here
- `tests/unit/test_case_number.py`: **EXECUTED, 5/5 pass** (pure stdlib logic).

## Written but NOT executable in this sandbox
Missing pytest/DB/Redis/Playwright/deps, so these are TEST WRITTEN only:
- Unit: otp, passwords, attachments, rate_limit (in-memory Redis), sla.
- Integration: ticket flow (ASGI+DB), message visibility, refresh rotation.
- E2E (Playwright): client journey, rate-limit 3-then-429, client scoping/security.

## How to run (with a real environment)
```bash
cd backend && pip install -e '.[dev]'
export TEST_DATABASE_URL=postgresql+asyncpg://... REDIS_URL=redis://...
pytest -q                       # unit + integration
ruff check . && mypy app        # lint + types
bandit -r app && pip-audit      # security
# frontend
cd ../frontend && npm ci && npx playwright install && npx playwright test
```
