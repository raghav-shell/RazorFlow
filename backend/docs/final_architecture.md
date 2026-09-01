# RazorFlow: Final Technical Architecture & System Documentation

RazorFlow is an institutional-grade, multi-tenant revenue recovery orchestration platform designed to recover lost revenue from failed transactions through AI root-cause diagnosis, deterministic financial policy authorization, bounded execution, and immutable cryptographic verification.

---

## 1. High-Level Architecture & Component Topology

```
+-----------------------------------------------------------------------------------+
|                            MERCHANT COMMAND CENTER (Next.js 16)                    |
|             Executive KPI Metrics | Case Investigation | Policy Studio | Audit    |
+-----------------------------------------------------------------------------------+
                                         │  HTTPS / JSON
                                         ▼
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                     |
|  Security Middleware | Request Tracing | Rate Limiting | Global Sanitized Handler |
|                                                                                   |
|  ┌─────────────────────┐   ┌───────────────────────────┐   ┌───────────────────┐  |
|  │  Webhook Ingestion  │   │   Order/Payment Sync      │   │  Case Aggregation │  |
|  │  HMAC-SHA256 Auth   │──▶│   Idempotent State Sync   │──▶│  Root Lifecycle   │  |
|  └─────────────────────┘   └───────────────────────────┘   └───────────────────┘  |
|                                                                      │            |
|                                                                      ▼            |
|  ┌─────────────────────┐   ┌───────────────────────────┐   ┌───────────────────┐  |
|  │  Tabular ML Model   │   │   ERV Ranker (Paise Math) │   │ Gemini AI Adapter │  |
|  │  recovery_model_v1  │──▶│   P_ML * Amount - Cost    │──▶│ gemini-3.6-flash  │  |
|  └─────────────────────┘   └───────────────────────────┘   └───────────────────┘  |
|                                                                      │            |
|                                                                      ▼            |
|  ┌─────────────────────────────────────────────────────────────────────────────┐  |
|  │                DETERMINISTIC POLICY ENGINE (Authoritative Gate)             │  |
|  │          Max Attempts | Cooldowns | High-Value Overrides | Disallowed       │  |
|  └─────────────────────────────────────────────────────────────────────────────┘  |
|                                         │                                         |
|                                         ▼                                         |
|  ┌─────────────────────────────────────────────────────────────────────────────┐  |
|  │                   ACTION ORCHESTRATOR & GATEWAY ADAPTERS                    │  |
|  │            Razorpay Test Gateway | SMS / WhatsApp Messaging Ports           │  |
|  └─────────────────────────────────────────────────────────────────────────────┘  |
|                                         │                                         |
|                                         ▼                                         |
|  ┌─────────────────────────────────────────────────────────────────────────────┐  |
|  │            VERIFICATION SERVICE & CRYPTOGRAPHIC AUDIT LEDGER                │  |
|  │            Settling Webhook Match | Sequential SHA-256 Hash Chain           │  |
|  └─────────────────────────────────────────────────────────────────────────────┘  |
+-----------------------------------------------------------------------------------+
              │                                                │
              ▼                                                ▼
+──────────────────────────────+             +──────────────────────────────────────+
|   SUPABASE POSTGRESQL        |             |   UPSTASH REDIS / CELERY WORKER      |
|   ACID Persistence Layer     |             |   Distributed Asynchronous Tasks     |
|   Row Locking (FOR UPDATE)   |             |   Scheduled Cooldown Reassessment    |
+──────────────────────────────+             +──────────────────────────────────────+
```

---

## 2. Decisioning & Financial Invariant Engine

RazorFlow enforces a strict separation of concerns across statistical modeling, generative reasoning, and financial authority:

```
                          CANDIDATE GENERATION
                                   ↓
                   TABULAR ML SCORER (recovery_model_v1)
                          P_ML ∈ [0.0, 1.0]
                                   ↓
                       DETERMINISTIC ERV RANKER
           Gross ERV = int(P_ML * Amount_at_risk_cents)
           Net ERV   = Gross ERV - Cost_cents - Risk_cents
                                   ↓
                  GEMINI AI REASONING (gemini-3.6-flash)
                          Advisory Strategy
                                   ↓
                DETERMINISTIC POLICY ENGINE (Authority)
               VERDICT: APPROVED | OVERRIDDEN | REJECTED
```

### Invariant 1: Generative AI is Advisory Only
- Gemini (`gemini-3.6-flash`) generates qualitative diagnosis and recommended actions.
- The **PolicyEngine** is the sole authority governing execution.
- If Gemini recommends an action that exceeds merchant risk thresholds, PolicyEngine overrides the proposal to `HUMAN_ESCALATION` or `REJECTED`.

### Invariant 2: Fault-Tolerant Deterministic Fallback
- If Gemini times out or encounters network partition, the decision pipeline transparently falls back to the top candidate from the **Deterministic ERV Ranker**.
- The business process never stalls due to AI availability issues.
- `is_fallback: true` and `fallback_reason` are immutably recorded in the decision model and audit ledger.

### Invariant 3: Pure Integer Minor-Unit Financial Precision
- All monetary calculations are performed in integer minor units (paise/cents).
- Floating-point calculations are strictly forbidden for balance, gross ERV, net ERV, and transaction state.

---

## 3. Cryptographic Audit Ledger (SHA-256 Hash Chain)

Every security-sensitive state transition, AI evaluation, policy check, and financial verification appends a tamper-evident audit event:

$$\text{Event Hash}_N = \text{SHA256}(\text{Canonical JSON}(\text{seq}_N, \text{prev\_hash}_{N-1}, \text{merchant\_id}, \text{action}, \text{payload}, \text{timestamp}))$$

- **Monotonic Sequence Numbers**: Enforced via PostgreSQL row-level locks (`SELECT ... FOR UPDATE`).
- **Genesis Hash**: The initial event links to `0` $\times 64$ (`GENESIS_PREV_HASH`).
- **Audit Verification Endpoint**: `GET /api/v1/audit/verify` checks the entire sequential chain to verify cryptographic integrity.

---

## 4. Synthetic Training Data vs Real Financial Records

RazorFlow maintains strict logical and physical separation between historical machine learning data and actual merchant financial transactions:

| Layer | Physical Location | Schema / Tagging | Usage |
|---|---|---|---|
| **Synthetic ML Training Data** | `backend/data/synthetic/recovery_history.csv` | Local CSV (10,000 records) | Offline model training only. Never written to Supabase. |
| **Serialized Model** | `backend/models/recovery_model_v1.joblib` | Scikit-learn pipeline | In-memory scoring inference. |
| **Demo Cohort Records** | Supabase Database | `metadata_json['is_demo'] = True`, `order_demo_*` | Evaluator demonstration. Safely purged by `POST /demo/reset-and-seed`. |
| **Real Merchant Transactions** | Supabase Database | Standard merchant UUIDs & Razorpay Payment IDs | Production & Test Mode financial recovery. |

---

## 5. Security & Deployment Posture

- **OWASP Security Headers**: Injected across all API responses (`X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Strict-Transport-Security`, `Referrer-Policy`, `Permissions-Policy`).
- **Sanitized Global Exception Handling**: Centralized handler intercepts all unhandled 500 errors, strips internal stack traces, and emits consistent JSON error responses with tracking `request_id`.
- **Fail-Closed Financial Gate**:
  - `RAZORPAY_MODE=test`
  - `RAZORPAY_PRODUCTION_ENABLED=false`
  - Execution strictly raises `PermissionError` if live keys or production flags are detected without verified authorization.
- **Container Hardening**: Dockerfiles for FastAPI, Celery, and Next.js execute under non-root users (`appuser` UID 10001, `nextjs` UID 10001).
