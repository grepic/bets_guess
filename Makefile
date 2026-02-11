.PHONY: up down build test migrate lint seed logs

# ─── Development ────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart api web

logs:
	docker compose logs -f --tail=100

logs-api:
	docker compose logs -f --tail=100 api

logs-worker:
	docker compose logs -f --tail=100 celery-worker

# ─── Database ───────────────────────────────────────────
migrate:
	alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-down:
	alembic downgrade -1

# ─── Testing ────────────────────────────────────────────
test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=apps/api --cov-report=term-missing

# ─── Linting ────────────────────────────────────────────
lint:
	python -m ruff check apps/ packages/ tests/

lint-fix:
	python -m ruff check --fix apps/ packages/ tests/

format:
	python -m ruff format apps/ packages/ tests/

# ─── Frontend ───────────────────────────────────────────
web-dev:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm run build

web-lint:
	cd apps/web && npm run lint

# ─── API (local) ────────────────────────────────────────
api-dev:
	uvicorn apps.api.main:app --reload --port 8000

# ─── Production Build ──────────────────────────────────
prod:
	docker compose -f docker-compose.yml build --target prod

# ─── Celery (local) ────────────────────────────────────
worker:
	celery -A apps.api.jobs.worker worker --loglevel=info --concurrency=2

beat:
	celery -A apps.api.jobs.worker beat --loglevel=info

# ─── Utilities ──────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true

help:
	@echo "SmartBets Pro - Available commands:"
	@echo ""
	@echo "  make up          - Start all services (docker)"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Build docker images"
	@echo "  make restart     - Restart api + web"
	@echo "  make logs        - Follow all logs"
	@echo ""
	@echo "  make migrate     - Run DB migrations"
	@echo "  make migrate-new - Create new migration"
	@echo ""
	@echo "  make test        - Run pytest"
	@echo "  make test-cov    - Run pytest with coverage"
	@echo "  make lint        - Run ruff linter"
	@echo "  make format      - Auto-format code"
	@echo ""
	@echo "  make api-dev     - Run API locally"
	@echo "  make web-dev     - Run frontend locally"
	@echo "  make worker      - Run Celery worker locally"
	@echo "  make beat        - Run Celery Beat locally"
	@echo ""
	@echo "  make clean       - Remove __pycache__ and .pyc"
