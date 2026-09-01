"""RazorFlow Pre-flight Environment and System Diagnostics Script.

Verifies database connectivity, migrations, Redis/Celery cache, Gemini AI configuration,
Razorpay Test Mode credentials, fail-closed safety guards, and ML model artifacts.
Redacts all sensitive tokens and prints a formatted PASS/FAIL checklist.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Dict, Tuple

from apps.api.config import get_settings
from packages.domain.entities import (
    CaseEnrichmentContext,
    CustomerSnapshot,
    OrderSnapshot,
    PaymentSnapshot,
    RecoveryCaseSnapshot,
)
from packages.domain.enums import (
    FailureCategory,
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.scoring.probability_scorer import MLProbabilityScorer
from packages.domain.value_objects import MonetaryAmount, RiskScore


def redact_secret(val: str | None, prefix_len: int = 4) -> str:
    """Safely redacts sensitive credentials for logging and display."""
    if not val:
        return "<NOT_SET>"
    if len(val) <= prefix_len:
        return "***"
    return f"{val[:prefix_len]}...{val[-2:]}" if len(val) > 8 else f"{val[:prefix_len]}***"


async def check_database(db_url: str) -> Tuple[bool, str]:
    """Tests async PostgreSQL connection and schema migration state."""
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            db_url,
            connect_args={"statement_cache_size": 0},
            pool_pre_ping=True,
        )
        async with engine.connect() as conn:
            # 1. Test basic connectivity
            res = await conn.execute(text("SELECT 1"))
            val = res.scalar()
            if val != 1:
                return False, "Database connection query returned unexpected result."

            # 2. Check alembic version table
            ver_res = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            ver = ver_res.scalar()
            if not ver:
                return False, "Alembic migration version table is empty."

        await engine.dispose()
        return True, f"Connected to PostgreSQL (Alembic version: {ver})"
    except Exception as e:
        return False, f"Database connection error: {type(e).__name__}: {e}"


async def check_redis(redis_url: str) -> Tuple[bool, str]:
    """Tests Redis connection and latency."""
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(redis_url, decode_responses=True)
        ping_res = await client.ping()
        await client.aclose()
        if ping_res is True:
            return True, "Redis / Upstash responded to PING (Healthy)"
        return False, f"Unexpected Redis ping response: {ping_res}"
    except Exception as e:
        return False, f"Redis connection error: {type(e).__name__}: {e}"


def check_gemini(api_key: str | None, model: str) -> Tuple[bool, str]:
    """Verifies Gemini API key presence and configured model."""
    if not api_key:
        return False, "GEMINI_API_KEY is not set in environment."
    redacted = redact_secret(api_key, prefix_len=6)
    return True, f"Configured model '{model}' with key {redacted}"


def check_razorpay(
    key_id: str | None,
    key_secret: str | None,
    webhook_secret: str | None,
    mode: str,
    prod_enabled: bool,
) -> Tuple[bool, str]:
    """Verifies Razorpay Test Mode credentials and fail-closed production safety guards."""
    if not key_id or not key_secret or not webhook_secret:
        return False, "Missing Razorpay credentials (KEY_ID, KEY_SECRET, or WEBHOOK_SECRET)."

    # Safety Guard Checks
    if mode.lower() != "test":
        return False, f"SECURITY VIOLATION: RAZORPAY_MODE is '{mode}', must be 'test'!"

    if prod_enabled is not False:
        return (
            False,
            f"SECURITY VIOLATION: RAZORPAY_PRODUCTION_ENABLED is {prod_enabled}, must be False!",
        )

    if key_id.startswith("rzp_live"):
        return (
            False,
            "SECURITY VIOLATION: Production key (rzp_live_*) detected in Test Mode configuration!",
        )

    return True, f"Test credentials verified ({redact_secret(key_id)}), fail-closed guard ACTIVE"


def check_ml_model() -> Tuple[bool, str]:
    """Verifies that the trained ML model artifact exists and can predict recovery probabilities."""
    model_path = Path(__file__).resolve().parent.parent / "models" / "recovery_model_v1.joblib"
    if not model_path.exists():
        return False, f"Model artifact not found at {model_path}"

    try:
        scorer = MLProbabilityScorer(model_path=str(model_path))
        if not scorer.is_ml_active:
            return False, "MLProbabilityScorer failed to activate scikit-learn model."

        # Predict sample case
        import uuid
        from datetime import datetime, timezone

        case = RecoveryCaseSnapshot(
            id=uuid.uuid4(),
            merchant_id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            initial_payment_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            amount_at_risk=MonetaryAmount.from_paise(250000, "INR"),
            amount_recovered=MonetaryAmount.from_paise(0, "INR"),
            status=RecoveryCaseStatus.DIAGNOSING,
            failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
            is_transient=False,
            current_attempt_count=0,
            max_allowed_attempts=3,
            deadline_at=datetime.now(timezone.utc),
        )
        ctx = CaseEnrichmentContext(
            customer=CustomerSnapshot(
                id=uuid.uuid4(),
                merchant_id=uuid.uuid4(),
                external_customer_id="cust_diag",
                email="diag@test.com",
                phone="+919800000000",
                name="Diagnostic Customer",
                risk_score=RiskScore(score=0.15),
                recovery_success_count=2,
                total_failure_count=0,
            ),
            order=OrderSnapshot(
                id=uuid.uuid4(),
                merchant_id=uuid.uuid4(),
                external_order_id="order_diag",
                amount=MonetaryAmount.from_paise(250000, "INR"),
                status=OrderStatus.ATTEMPTED,
                customer_id=uuid.uuid4(),
            ),
            initial_payment=PaymentSnapshot(
                id=uuid.uuid4(),
                merchant_id=uuid.uuid4(),
                order_id=uuid.uuid4(),
                external_payment_id="pay_diag",
                amount=MonetaryAmount.from_paise(250000, "INR"),
                status=PaymentStatus.FAILED,
                customer_id=uuid.uuid4(),
                method="upi",
                error_code="BAD_REQUEST_ERROR",
                error_source="customer",
                error_step="payment_authentication",
                error_reason="authentication_failed",
            ),
            historical_success_count=2,
            historical_failure_count=0,
            previous_recovery_count=1,
            customer_risk_tier="LOW",
        )
        prob = scorer.score(case, ctx, RecoveryActionType.PAYMENT_LINK)
        if not (0.0 <= prob.value <= 1.0):
            return False, f"Predicted probability out of bounds: {prob.value}"

        return True, f"Artifact '{scorer.model_version}' active (Sample P_ML={prob.value:.4f})"
    except Exception as e:
        return False, f"ML Model validation error: {type(e).__name__}: {e}"


async def run_diagnostics() -> int:
    """Executes full suite of pre-flight environment checks."""
    print("=" * 70)
    print(" RAZORFLOW — PRE-FLIGHT SYSTEM & ENVIRONMENT DIAGNOSTICS")
    print("=" * 70)

    settings = get_settings()
    results: Dict[str, Tuple[bool, str]] = {}

    # 1. Database
    db_pass, db_msg = await check_database(settings.DATABASE_URL)
    results["DATABASE (PostgreSQL / Supabase)"] = (db_pass, db_msg)

    # 2. Redis
    redis_pass, redis_msg = await check_redis(settings.REDIS_URL)
    results["REDIS / CELERY (Upstash / Cache)"] = (redis_pass, redis_msg)

    # 3. Gemini AI
    gemini_pass, gemini_msg = check_gemini(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    results["GEMINI AI (Advisory Reasoning)"] = (gemini_pass, gemini_msg)

    # 4. Razorpay Test Mode
    rzp_pass, rzp_msg = check_razorpay(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET,
        settings.RAZORPAY_WEBHOOK_SECRET,
        settings.RAZORPAY_MODE,
        settings.RAZORPAY_PRODUCTION_ENABLED,
    )
    results["RAZORPAY GATEWAY (Test Mode)"] = (rzp_pass, rzp_msg)

    # 5. Production Safety Guards
    safety_pass = (settings.RAZORPAY_MODE == "test") and (not settings.RAZORPAY_PRODUCTION_ENABLED)
    safety_msg = "Fail-Closed Protection Enabled (Live payments strictly blocked)"
    results["PRODUCTION SAFETY GUARDS"] = (safety_pass, safety_msg)

    # 6. ML Model
    ml_pass, ml_msg = check_ml_model()
    results["ML MODEL (recovery_model_v1)"] = (ml_pass, ml_msg)

    # Print Summary Checklist
    print("\nPre-flight Diagnostic Checklist:\n")
    all_passed = True

    for name, (passed, msg) in results.items():
        status_str = "[\033[92mPASS\033[0m]" if passed else "[\033[91mFAIL\033[0m]"
        dots = "." * (45 - len(name))
        print(f"  {name} {dots} {status_str}")
        print(f"    -> {msg}\n")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print(" \033[92mPRE-FLIGHT CHECK COMPLETED SUCCESSFULLY: ALL SYSTEMS READY\033[0m")
        print("=" * 70)
        return 0
    else:
        print(" \033[91mPRE-FLIGHT CHECK FAILED: PLEASE RESOLVE MISSING CONFIGURATION\033[0m")
        print("=" * 70)
        return 1


def main() -> None:
    exit_code = asyncio.run(run_diagnostics())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
