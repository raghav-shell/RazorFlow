# RazorFlow: Intelligent Revenue Recovery Orchestrator

RazorFlow is an institutional-grade revenue recovery orchestration platform for merchants, designed to recover lost revenue from failed transactions using AI-driven root-cause reasoning, deterministic financial policy authorization, bounded execution, and immutable cryptographic verification.

---

## Architectural Lifecycle

```
FAILED PAYMENT (Razorpay Webhook)
        ↓
SIGNATURE VERIFICATION (Constant-time HMAC-SHA256)
        ↓
RAW EVENT PERSISTENCE (Durable Idempotency)
        ↓
ORDER / PAYMENT RECONCILIATION
        ↓
RECOVERY CASE AGGREGATE
        ↓
CUSTOMER CONTEXT ENRICHMENT
        ↓
ML PROBABILITY (P) & ERV CALCULATION (P * Value - Cost - Risk)
        ↓
GEMINI AI STRATEGY (Advisory Reasoning — gemini-3.6-flash)
        ↓
DETERMINISTIC POLICY ENGINE (Authoritative Guardrails & State Machine)
        ↓
ACTION ORCHESTRATOR (Row-level Locking & Idempotent Commands)
        ↓
PROVIDER ADAPTER (Razorpay Test Mode / SMS / WhatsApp)
        ↓
FINANCIAL VERIFICATION (Settling Webhook Reconciliation)
        ↓
IMMUTABLE AUDIT LEDGER (Sequential SHA-256 Hash Chain)
        ↓
MERCHANT COMMAND CENTER (Next.js 16)
```

---

## Production Monorepo Structure

```
RazorFlow/
├── backend/
│   ├── apps/
│   │   ├── api/             # FastAPI API (Routes, Middleware, Security, Lifespan)
│   │   └── worker/          # Celery Distributed Task Worker & Scheduled Reassessment
│   ├── packages/
│   │   ├── adapters/        # Razorpay Test Adapter, Gemini AI Adapter, Mock Adapters
│   │   ├── domain/          # Pure Domain Entities, Policies, State Machine, ERV, Value Objects
│   │   ├── orchestration/   # Decision Service, Action Executors, Verification Service
│   │   ├── persistence/     # SQLAlchemy Async ORM Models, Migrations, Audit Ledger
│   │   └── ports/           # Provider-Agnostic Gateways & Messaging Interfaces
│   ├── scripts/
│   │   └── verify_razorpay_test_flow.py # Standalone Live Razorpay Test Mode Verification
│   ├── tests/               # 124 Unit, Integration, Concurrency & Security Tests
│   ├── alembic/             # Database Schema Migrations
│   ├── pyproject.toml       # Python Dependencies and Build Metadata
│   └── Makefile             # Backend-scoped Automation Runners
├── frontend/                # Next.js 16 Merchant Command Center (React, Tailwind CSS v4, Lucide)
├── docker-compose.yml       # Production-Ready Multi-Container Stack (Non-root users)
├── Makefile                 # Top-level Orchestrator Shortcuts
└── README.md                # System Documentation & Runbook
```

---

## Environment Variable Reference

| Variable Name | Purpose | Required? | Scope | Where to Obtain | Example Value |
|---|---|---|---|---|---|
| `ENVIRONMENT` | Runtime mode (`development`, `staging`, `production`, `test`) | Yes | Backend | System environment | `production` |
| `DEBUG` | Enables debug logging and interactive OpenAPI docs | Optional | Backend | System environment | `false` |
| `LOG_LEVEL` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | Optional | Backend | System environment | `INFO` |
| `SECRET_KEY` | Symmetric token signing secret (min 32 characters) | Yes | Backend | Generated random string | `super-secret-key-32chars-min!!` |
| `ENCRYPTION_KEY` | 32-byte key for encrypting provider credentials at rest | Yes | Backend | Base64-encoded 32-byte key | `32-bytes-base64-encryption-key!` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed CORS origins | Yes (Prod) | Backend | Frontend deployment URLs | `https://razorflow.domain.com,https://app.vercel.app` |
| `DATABASE_URL` | PostgreSQL connection string with `asyncpg` driver | Yes | Backend | Supabase / Database Provider | `postgresql+asyncpg://postgres:[PASS]@[HOST]:5432/postgres` |
| `DATABASE_SYNC_URL` | Synchronous PostgreSQL connection string for Alembic | Optional | Backend | Supabase / Database Provider | `postgresql://postgres:[PASS]@[HOST]:5432/postgres` |
| `REDIS_URL` | Redis instance connection string for state caching | Yes | Backend | Upstash / Redis Provider | `rediss://default:[PASS]@[HOST]:6379/0` |
| `CELERY_BROKER_URL` | Redis broker URI for Celery background tasks | Yes | Backend | Upstash / Redis Provider | `rediss://default:[PASS]@[HOST]:6379/1` |
| `CELERY_RESULT_BACKEND` | Redis backend URI for Celery task results | Yes | Backend | Upstash / Redis Provider | `rediss://default:[PASS]@[HOST]:6379/2` |
| `GEMINI_API_KEY` | Google Gemini API key for AI strategy recommendations | Yes | Backend Only | Google AI Studio | `AIzaSy...` |
| `GEMINI_MODEL` | Gemini LLM model identifier | Optional | Backend | Google Gemini documentation | `gemini-3.6-flash` |
| `AI_TIMEOUT_SECONDS` | Timeout before deterministic ERV fallback activates | Optional | Backend | System tuning (default 8.0s) | `8.0` |
| `AI_ENABLED` | Feature flag to toggle AI strategy module | Optional | Backend | System configuration | `true` |
| `RAZORPAY_MODE` | Gateway operational mode (Must be `test`) | Yes | Backend | Razorpay configuration | `test` |
| `RAZORPAY_PRODUCTION_ENABLED`| Fail-closed live charge prevention flag | Yes | Backend | Must remain `false` | `false` |
| `RAZORPAY_KEY_ID` | Razorpay Test API Key ID | Yes | Backend Only | Razorpay Dashboard (Test Mode) | `rzp_test_xxxxxxxxxxxxxx` |
| `RAZORPAY_KEY_SECRET` | Razorpay Test API Key Secret | Yes | Backend Only | Razorpay Dashboard (Test Mode) | `your_secret_here` |
| `RAZORPAY_WEBHOOK_SECRET` | Secret for HMAC-SHA256 webhook signature check | Yes | Backend Only | Razorpay Webhook Settings | `your_whsec_here` |
| `NEXT_PUBLIC_API_URL` | Public backend API URL queried by Next.js frontend | Yes | Frontend (Public) | Cloud backend domain / ngrok | `http://localhost:8000/api/v1` |

---

## Local Development & Quickstart

### 1. Install Dependencies
```bash
# Python Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e "./backend[dev]"

# Next.js Frontend
cd frontend
npm install
cd ..
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Run Database Migrations
```bash
make migrate
```

### 4. Start Application Services
```bash
# Option A: Root Makefile runners (separate terminal tabs)
make run-api       # Runs FastAPI backend on :8000
make run-worker    # Runs Celery task worker
make run-frontend  # Runs Next.js frontend on :3000

# Option B: Docker Compose Stack (All services with non-root security)
docker compose up --build -d
```

- **Frontend Command Center**: `http://localhost:3000`
- **Backend Swagger API Docs**: `http://localhost:8000/docs`
- **API Health Check**: `http://localhost:8000/health`

---

## Automated Verification Suite

Run the full automated test and quality verification suite from the project root:

```bash
make test          # Runs 124 unit, integration, concurrency, and security tests with coverage
make lint          # Runs ruff linter, code formatter check, and mypy static type analysis
make format        # Automatically formats codebase according to standards
cd frontend && npm run build # Compiles and verifies Next.js 16 production build
```

---

## Real Razorpay Test Mode Verification

RazorFlow includes a dedicated, fail-closed live verification script that performs an authentic end-to-end recovery run against Razorpay's Test API and Gemini AI:

```bash
.venv/bin/python backend/scripts/verify_razorpay_test_flow.py
```

### Verification Flow Performed:
1. **Fail-Closed Guard Check**: Verifies `RAZORPAY_MODE=test` and `RAZORPAY_PRODUCTION_ENABLED=false`. Rejects execution if live credentials are provided.
2. **Merchant Provisioning**: Configures tenant with encrypted test credentials.
3. **Webhook Ingestion**: Generates and ingests HMAC-SHA256 signed `payment.failed` event.
4. **Case Creation**: Synchronizes Order, Payment, Customer, and RecoveryCase aggregate root.
5. **AI Strategy Formulation**: Queries configured Gemini AI model (`gemini-3.6-flash`) with structured output schemas and deterministic ERV ranking.
6. **Policy Authorization**: Deterministic PolicyEngine enforces merchant constraints and state transitions.
7. **Real Payment Link Creation**: Calls Razorpay Test API to generate an authentic hosted payment link (`https://rzp.io/rzp/...`).
8. **Financial Verification**: Ingests `payment.captured` event, verifies funds, and transitions case to `RECOVERED`/`APPROVED`.
9. **Cryptographic Audit Check**: Validates that all events are immutably recorded in a sequential SHA-256 hash chain starting from the genesis hash (`000000...`).

---

## Security & Reliability Posture

- **OWASP Security Headers**: Injected automatically on all API responses (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`).
- **Sanitized Exception Handling**: Global 500 handler strips all internal stack traces and secrets, returning a consistent JSON error with a tracing `request_id`.
- **Startup Safety Validator**: Automatically aborts startup in production if default secrets, wildcard CORS origins, or insecure configurations are detected.
- **Fail-Closed Financial Guards**: Hardcoded gate checks prevent any live financial mutations unless strict multi-layered production overrides are satisfied.
- **Credential Encryption at Rest**: Provider secrets and API keys are stored encrypted using symmetric AES-GCM envelopes.
- **Container Hardening**: All Docker images execute under dedicated non-root users (`appuser` UID 10001, `nextjs` UID 10001) with multi-stage build caching.
- **Supabase Connection Pooling**: Configured with `statement_cache_size=0` for full compatibility with Supabase Supavisor/PgBouncer transaction poolers.
