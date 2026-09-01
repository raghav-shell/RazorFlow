.PHONY: help install test lint format run-api run-worker run-frontend docker-up docker-down migrate

VENV := $(shell pwd)/.venv
BIN := $(VENV)/bin

help:
	@echo "RazorFlow Monorepo Commands:"
	@echo "  make install       - Install Python backend dependencies in editable mode"
	@echo "  make test          - Run full backend pytest test suite"
	@echo "  make lint          - Run backend ruff and mypy linters"
	@echo "  make format        - Auto-format backend with ruff"
	@echo "  make run-api       - Run FastAPI server locally with reload"
	@echo "  make run-worker    - Run Celery background worker"
	@echo "  make run-frontend  - Run Next.js frontend dev server"
	@echo "  make docker-up     - Start PostgreSQL & Redis services via Docker Compose"
	@echo "  make docker-down   - Stop all Docker services"
	@echo "  make migrate       - Run Alembic database migrations"

install:
	$(BIN)/pip install -e ./backend"[dev]"

test:
	cd backend && $(BIN)/pytest -v --cov=packages --cov=apps

lint:
	cd backend && $(BIN)/ruff check . && $(BIN)/mypy packages apps

format:
	cd backend && $(BIN)/ruff format .

run-api:
	cd backend && $(BIN)/uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	cd backend && $(BIN)/celery -A apps.worker.celery_app.celery_app worker --loglevel=info -c 2

run-frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up -d postgres redis

docker-down:
	docker compose down

migrate:
	cd backend && $(BIN)/alembic upgrade head
