.PHONY: help up down build migrate seed-demo test test-api test-web lint import-registry clean

help:
	@echo "Available commands:"
	@echo "  make up               - Start Docker compose stack"
	@echo "  make down             - Stop Docker compose stack"
	@echo "  make build            - Build Docker images"
	@echo "  make migrate          - Run database migrations"
	@echo "  make seed-demo        - Seed demo fixtures and registry"
	@echo "  make test             - Run backend and frontend test suites"
	@echo "  make lint             - Run linters (ruff, eslint)"
	@echo "  make import-registry  - Import VASP registry (Phase 2)"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

migrate:
	cd services/api && alembic upgrade head

seed-demo:
	cd services/api && python -m app.scripts.seed_demo

test: test-api test-web

test-api:
	cd services/api && pytest

test-web:
	cd apps/web && npm test --if-present

lint:
	cd services/api && ruff check .
	cd apps/web && npm run lint

import-registry:
	@echo "Importing registry from $(FILE)..."
	cd services/api && .venv/Scripts/python.exe -m app.scripts.import_registry $(FILE)

clean:
	docker compose down -v
	rm -rf apps/web/.next apps/web/node_modules services/api/.pytest_cache
