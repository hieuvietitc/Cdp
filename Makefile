.PHONY: up down build migrate seed logs ps clean test backup monitor

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

# ─── Backup ───────────────────────────────────────────────────────────────
backup:
	docker compose exec backup /backup.sh

# ─── Monitoring ───────────────────────────────────────────────────────────
monitor:
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3001  (admin / see GRAFANA_PASSWORD in .env)"
	@echo "Superset:   http://localhost:8088  (admin / see SUPERSET_ADMIN_PASSWORD)"
	@echo ""
	@docker compose exec prometheus wget -qO- http://localhost:9090/-/healthy || echo "Prometheus not running"

stream-lag:
	@docker compose exec redis redis-cli XLEN cdp:events

setup: build migrate sdk-build up
	@echo ""
	@echo "CDP system ready."
	@echo "  Admin UI:   http://localhost:3000"
	@echo "  Admin API:  http://localhost:8002/docs"
	@echo "  Grafana:    http://localhost:3001"
	@echo "  Superset:   http://localhost:8088"
	@echo "  Prometheus: http://localhost:9090"
	@echo ""
	@echo "Next: create first admin user via POST /api/v1/auth/users"
