.PHONY: help up down logs migrate seed test lint typecheck security fmt

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-12s %s\n", $$1, $$2}'

up: ## Start the dev stack
	docker compose up --build

down: ## Stop the stack
	docker compose down

logs: ## Tail logs
	docker compose logs -f

migrate: ## Run DB migrations
	docker compose exec api alembic upgrade head

seed: ## Seed reference data + admin
	docker compose exec api python -m app.seed

test: ## Run backend tests
	cd backend && pytest -q

lint: ## Ruff lint
	cd backend && ruff check .

typecheck: ## mypy
	cd backend && mypy app

security: ## Bandit + pip-audit
	cd backend && bandit -r app -q && pip-audit

fmt: ## Ruff format
	cd backend && ruff format .
