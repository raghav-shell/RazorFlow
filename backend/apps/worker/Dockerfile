FROM python:3.11-slim

WORKDIR /app

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libc-dev && rm -rf /var/lib/apt/lists/*

# Create non-root system user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

COPY pyproject.toml README.md ./
COPY packages/ ./packages/
COPY apps/ ./apps/
COPY alembic.ini ./

RUN pip install --no-cache-dir -e . && \
    chown -R appuser:appgroup /app

USER appuser

CMD ["celery", "-A", "apps.worker.celery_app.celery_app", "worker", "--loglevel=info", "-c", "2"]
