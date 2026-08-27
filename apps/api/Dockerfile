FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc libc-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY packages/ ./packages/
COPY apps/ ./apps/
COPY alembic.ini ./

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
