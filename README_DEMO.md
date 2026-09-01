# RazorFlow: 5-Minute Evaluator Demo Runbook

This runbook guides evaluators through an end-to-end walkthrough of RazorFlow's autonomous revenue recovery platform in under 5 minutes.

---

## 1. Start Services & Verify Pre-flight Status

### Option A: Local Development Run (3 Terminal Tabs)
```bash
# Terminal 1: FastAPI Backend
make run-api

# Terminal 2: Celery Worker
make run-worker

# Terminal 3: Next.js Frontend
make run-frontend
```

### Option B: Docker Compose (All Services)
```bash
docker compose up --build -d
```

### Run System Pre-flight Check
Run the automated diagnostic check to verify all connections (Supabase, Upstash Redis, Gemini, Razorpay Test API, ML Model):
```bash
source .venv/bin/activate
python backend/scripts/preflight_check.py
```
*Expected Output: `PRE-FLIGHT CHECK COMPLETED SUCCESSFULLY: ALL SYSTEMS READY`*

---

## 2. Seed Clean Demo Cohort (22 Realistic Cases)

Reset and seed a clean cohort of 22 realistic demo payment failures across all recovery categories:
```bash
curl -X POST "http://localhost:8000/api/v1/demo/reset-and-seed?merchant_slug=demo-store"
```

Open the Merchant Command Center at: **`http://localhost:3000`**

---

## 3. Evaluator Scenarios Walkthrough

### Scenario 1: Autonomous Payment Link Recovery (End-to-End)
Demonstrates the full autonomous recovery loop: failed payment $\rightarrow$ ML $P_{ML}$ $\rightarrow$ ERV calculation $\rightarrow$ Gemini AI strategy formulation $\rightarrow$ PolicyEngine authorization $\rightarrow$ Razorpay Test payment link creation $\rightarrow$ simulated customer payment $\rightarrow$ financial verification $\rightarrow$ cryptographic audit ledger.

```bash
curl -X POST "http://localhost:8000/api/v1/demo/seed?merchant_slug=demo-store" \
     -H "Content-Type: application/json" \
     -d '{"scenario_id": "scenario_1"}'
```
**Key Highlights**:
- **Recovered Amount**: ₹4,500.00 (Net Recovered: ₹4,498.00 after ₹2.00 link cost).
- **Status**: Transitions to `RECOVERED` / `APPROVED`.
- **View in UI**: Refresh `http://localhost:3000` to see total recovered revenue increase, then click the recovered case to view the complete visual timeline.

---

### Scenario 2: Transient Bank Outage Cooldown (`WAIT_AND_REASSESS`)
Demonstrates intelligent failure classification and cooldown enforcement during bank outages to prevent blind customer spamming.

```bash
curl -X POST "http://localhost:8000/api/v1/demo/seed?merchant_slug=demo-store" \
     -H "Content-Type: application/json" \
     -d '{"scenario_id": "scenario_2"}'
```
**Key Highlights**:
- **Diagnosis**: HDFC Bank UPI gateway unreachable (503 Service Unavailable).
- **Action**: Enforces a 30-minute cooldown period (`WAIT_AND_REASSESS`).
- **Status**: Transitions to `WAITING_EXTERNAL` with `next_action_scheduled_at`.

---

### Scenario 3: High-Value Policy Override (AI Advisory vs Policy Authority)
Demonstrates strict policy guardrails overriding Gemini AI recommendations when business risk thresholds are exceeded.

```bash
curl -X POST "http://localhost:8000/api/v1/demo/seed?merchant_slug=demo-store" \
     -H "Content-Type: application/json" \
     -d '{"scenario_id": "scenario_3"}'
```
**Key Highlights**:
- **Amount**: ₹85,000.00 (exceeds high-value threshold of ₹50,000.00).
- **Gemini Recommendation**: `PAYMENT_LINK` (Advisory).
- **PolicyEngine Verdict**: `OVERRIDDEN` $\rightarrow$ Authorized Action: `HUMAN_ESCALATION`.
- **Audit Verification**: Both the AI recommendation and the final policy override rule code (`RULE_HIGH_VALUE_ESCALATION`) are immutably logged in the audit trail.

---

### Scenario 4: AI Failure Fallback to Deterministic ERV
Demonstrates financial system resilience when the Gemini API is unreachable or times out.

```bash
curl -X POST "http://localhost:8000/api/v1/demo/seed?merchant_slug=demo-store" \
     -H "Content-Type: application/json" \
     -d '{"scenario_id": "scenario_4"}'
```
**Key Highlights**:
- **Simulated Event**: Gemini timeout / network partition.
- **System Behavior**: Transparently falls back to deterministic ERV candidate ranking without dropping or failing the transaction.
- **Audit Metadata**: `is_fallback: true` and `fallback_reason: "AI_TIMEOUT"` recorded for governance.

---

## 4. Live Razorpay Test Mode Verification

Execute the authentic live verification script against real Razorpay Test API and Gemini AI:
```bash
python backend/scripts/verify_razorpay_test_flow.py
```
**Verifies**:
- Real Razorpay Test Payment Link creation (e.g. `https://rzp.io/rzp/...`).
- Simulated payment capture and webhook ingestion with valid HMAC-SHA256 signature.
- Cryptographic SHA-256 hash chaining back to genesis.

---

## 5. Inspect Cryptographic Audit Ledger

Verify that the entire sequence of recovery decisions and state mutations forms an unbroken cryptographic SHA-256 hash chain:

```bash
curl "http://localhost:8000/api/v1/audit/verify?merchant_slug=demo-store"
```

**Expected Response**:
```json
{
  "merchant_slug": "demo-store",
  "is_valid": true,
  "total_events": 28,
  "genesis_hash": "d23f4e360bcf8547...",
  "latest_hash": "1964a8ddcb9b6f52...",
  "broken_at_sequence": null,
  "status": "SECURE_UNBROKEN_CHAIN"
}
```

Or open the **Audit Ledger Explorer** directly in the browser: **`http://localhost:3000/audit`**.
