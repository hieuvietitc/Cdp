.PHONY: up down build migrate seed logs ps clean test

# ─── Dev lifecycle ────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

# ─── Database ─────────────────────────────────────────────────────────────
migrate:
	docker compose run --rm migrate

migrate-create:
	docker compose run --rm migrate alembic revision --autogenerate -m "$(name)"

migrate-down:
	docker compose run --rm migrate alembic downgrade -1

# ─── Development helpers ──────────────────────────────────────────────────
shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec postgres psql -U cdp cdpdb

# ─── SDK build ────────────────────────────────────────────────────────────
sdk-build:
	cd sdk/js && npm install && npm run build

# ─── Tests ────────────────────────────────────────────────────────────────
test:
	docker compose run --rm collector pytest services/collector/tests
	docker compose run --rm processor pytest services/processor/tests
	docker compose run --rm api pytest services/api/tests

# ─── Cleanup ──────────────────────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans

setup: build migrate sdk-build up
	@echo "CDP system ready. Admin UI: http://localhost:3000"
