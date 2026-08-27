FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libc-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY packages/ ./packages/
COPY apps/ ./apps/
COPY alembic.ini ./

RUN pip install --no-cache-dir -e .

CMD ["celery", "-A", "apps.worker.celery_app.celery_app", "worker", "--loglevel=info", "-c", "2"]
