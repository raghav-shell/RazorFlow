# RazorFlow Backend

The core Python backend layer for RazorFlow: an institutional-grade revenue recovery orchestration platform for Razorpay.

---

## Directory Architecture

```
backend/
├── apps/
│   ├── api/                 # FastAPI REST application & endpoints
│   │   ├── routes/v1/       # Versioned API routes (cases, decisions, policies, demo, metrics, audit)
│   │   ├── config.py        # Strongly-typed Pydantic settings & environment configuration
│   │   ├── dependencies.py  # Dependency injection (Database async session & Redis pool)
│   │   └── main.py          # FastAPI application factory and lifespan manager
│   └── worker/              # Celery background worker for asynchronous task dispatch
│       ├── celery_app.py    # Celery configuration with TLS & zero-loss guarantees
│       └── tasks/           # Ingestion and health worker tasks
├── packages/                # Clean / Hexagonal Architecture Domain Packages
│   ├── domain/              # Pure business logic (Entities, Value Objects, Policies, Scoring, Strategies)
│   ├── ports/               # Abstract interfaces (PaymentGatewayPort, MessagingPort, AIPort)
│   ├── adapters/            # Concrete integrations (Razorpay API, Gemini AI, Webhook Verifier)
│   ├── orchestration/       # Application services (ActionOrchestrator, VerificationService, DecisionService)
│   ├── persistence/         # SQLAlchemy 2.0 async models, Alembic migrations, and Audit Ledger
│   └── common/              # Cryptographic primitives (HMAC, SHA-256 hash chains)
├── tests/                   # Automated Unit, Integration, and Concurrency Test Suites
├── alembic.ini              # Database migration configuration
├── pyproject.toml           # Python dependencies, Ruff, Mypy, and Pytest configuration
└── Makefile                 # Backend development shortcuts
```

---

## Local Development & Testing

```bash
# Run test suite with code coverage
pytest -v --cov=packages --cov=apps

# Run code formatting and linting
ruff check .
ruff format --check .
mypy packages apps scripts

# Run Alembic migrations
alembic upgrade head

# Run API server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run Celery worker
celery -A apps.worker.celery_app.celery_app worker --loglevel=info -c 2
```
