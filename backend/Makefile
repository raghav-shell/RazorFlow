.PHONY: help install test lint format run-api run-worker docker-up docker-down migrate

help:
	@echo "RazorFlow Development Commands:"
	@echo "  make install      - Install Python dependencies in editable mode"
	@echo "  make test         - Run full pytest test suite"
	@echo "  make lint         - Run ruff and mypy linters"
	@echo "  make format       - Auto-format with ruff"
	@echo "  make run-api      - Run FastAPI server locally with reload"
	@echo "  make run-worker   - Run Celery background worker"
	@echo "  make docker-up    - Start PostgreSQL & Redis services via Docker Compose"
	@echo "  make docker-down  - Stop all Docker services"
	@echo "  make migrate      - Run Alembic database migrations"

install:
	pip install -e ".[dev]"

test:
	pytest -v --cov=packages --cov=apps

lint:
	ruff check .
	mypy packages apps

format:
	ruff format .

run-api:
	uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	celery -A apps.worker.celery_app.celery_app worker --loglevel=info -c 2

docker-up:
	docker-compose up -d postgres redis

docker-down:
	docker-compose down

migrate:
	alembic upgrade head
