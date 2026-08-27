# RazorFlow: Institutional-Grade Revenue Recovery Orchestrator

RazorFlow is an intelligent revenue-recovery orchestration layer for merchants, designed to maximize **Incremental Revenue Recovered** through AI-assisted strategy recommendation, deterministic financial policy authorization, autonomous execution, and cryptographically verified financial auditing.

---

## Architectural Principles (Hexagonal / Clean Architecture)

```
[ Domain Layer ]  (Pure Python: States, Entities, Invariants, State Machines)
       ↓
[ Application Layer ]  (Action Orchestrator, Verification Service, Use Cases)
       ↓
[ Ports Layer ]  (Abstract PaymentGatewayPort, MessagingPort)
       ↓
[ Adapters Layer ]  (Razorpay Client, WhatsApp/SMS Client, Database Repositories)
       ↓
[ External Rails ]  (Razorpay APIs, Webhooks, PostgreSQL, Redis)
```

- **Deterministic Financial Policy Gatekeeper**: AI proposes strategy $\rightarrow$ Policy Engine authorizes $\rightarrow$ Action Orchestrator executes.
- **PostgreSQL Source of Truth**: Financial idempotency and race condition prevention are enforced strictly via database unique constraints, partial active-case indexes, and row-level atomic state transitions.
- **Append-Only Cryptographic Hash-Chain Ledger**: Every state transition and decision rationale is secured in a SHA-256 hash chain per tenant.

---

## Local Development Quickstart

### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Make (optional, for CLI shortcuts)

### 2. Environment Setup
```bash
# Clone and enter workspace
cd RazorFlow

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in development/editable mode
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
```

### 3. Launch Local Infrastructure (PostgreSQL & Redis)
```bash
docker-compose up -d postgres redis
```

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Start API Server & Celery Worker
```bash
# Terminal 1: FastAPI Server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Celery Background Worker
celery -A apps.worker.celery_app.celery_app worker --loglevel=info -c 2
```

The API docs are available at `http://localhost:8000/docs`.

---

## Testing & Quality Assurance

```bash
# Run unit & integration tests
pytest

# Run linters and type checkers
ruff check .
mypy packages apps
```
