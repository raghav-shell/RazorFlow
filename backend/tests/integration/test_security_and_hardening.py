"""Integration tests for Phase 6 Security, Middleware, Exception Redaction, and Production Hardening."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from apps.api.config import Settings
from apps.api.main import create_app
from apps.worker.tasks.ingestion import _reassess_scheduled_cases_async
from packages.domain.enums import FailureCategory, OrderStatus, PaymentStatus, RecoveryCaseStatus
from packages.persistence.base import Base
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)


def test_security_headers_injected_on_responses(test_client: TestClient):
    """Verifies that OWASP security headers and request tracing headers are present on responses."""
    response = test_client.get("/healthz")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Permissions-Policy") is not None
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-MS" in response.headers


def test_global_unhandled_exception_handler_sanitizes_errors():
    """Verifies that unhandled exceptions do not leak stack traces or raw errors."""
    app = create_app()

    @app.get("/test-internal-error")
    async def trigger_error():
        raise RuntimeError("DATABASE_PASSWORD=supersecret_internal_pass_leak!")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-internal-error")
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "Internal Server Error"
    assert "supersecret" not in response.text
    assert "DATABASE_PASSWORD" not in response.text
    assert "request_id" in data


def test_production_config_safety_validator():
    """Verifies validate_production_safety blocks insecure settings in production mode."""
    # 1. Insecure default SECRET_KEY in production
    insecure_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="dev-insecure-secret-key-32chars-min!!",
        ENCRYPTION_KEY="dev-insecure-encryption-key-32ch!",
        CORS_ALLOWED_ORIGINS="https://app.razorflow.com",
    )
    with pytest.raises(ValueError, match="Default SECRET_KEY detected in production"):
        insecure_settings.validate_production_safety()

    # 2. Wildcard CORS in production
    wildcard_cors_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="prod-strong-secret-key-32-chars-long!",
        ENCRYPTION_KEY="prod-strong-encryption-key-32-ch!",
        CORS_ALLOWED_ORIGINS="*",
    )
    with pytest.raises(ValueError, match="Wildcard CORS origin is forbidden in production"):
        wildcard_cors_settings.validate_production_safety()

    # 3. Valid production configuration must not raise
    valid_prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="prod-strong-secret-key-32-chars-long!",
        ENCRYPTION_KEY="prod-strong-encryption-key-32-ch!",
        CORS_ALLOWED_ORIGINS="https://app.razorflow.com,https://api.razorflow.com",
        DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db",
        CELERY_BROKER_URL="rediss://user:pass@host:6379/1",
    )
    valid_prod_settings.validate_production_safety()


@pytest.mark.asyncio
async def test_celery_scheduled_cases_reassessment():
    """Verifies that expired WAITING_EXTERNAL cases are identified and transitioned to ANALYZING."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        merchant = MerchantModel(
            name="Test Store", slug="test-store", currency="INR", is_active=True
        )
        session.add(merchant)
        await session.flush()

        order1 = OrderModel(
            merchant_id=merchant.id,
            external_order_id="order_exp_1",
            amount_cents=50000,
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        order2 = OrderModel(
            merchant_id=merchant.id,
            external_order_id="order_fut_2",
            amount_cents=75000,
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        session.add_all([order1, order2])
        await session.flush()

        payment1 = PaymentModel(
            merchant_id=merchant.id,
            order_id=order1.id,
            external_payment_id="pay_exp_1",
            amount_cents=50000,
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
        )
        payment2 = PaymentModel(
            merchant_id=merchant.id,
            order_id=order2.id,
            external_payment_id="pay_fut_2",
            amount_cents=75000,
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
        )
        session.add_all([payment1, payment2])
        await session.flush()

        # Case 1: Expired delay (10 minutes in the past) -> Should transition to ANALYZING
        past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        deadline = datetime.now(timezone.utc) + timedelta(hours=72)
        case_expired = RecoveryCaseModel(
            merchant_id=merchant.id,
            order_id=order1.id,
            initial_payment_id=payment1.id,
            amount_at_risk_cents=50000,
            currency="INR",
            failure_category=FailureCategory.TECHNICAL_GATEWAY_TIMEOUT,
            status=RecoveryCaseStatus.WAITING_EXTERNAL,
            next_action_scheduled_at=past_time,
            deadline_at=deadline,
        )
        # Case 2: Future delay (30 minutes in the future) -> Should remain WAITING_EXTERNAL
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        case_future = RecoveryCaseModel(
            merchant_id=merchant.id,
            order_id=order2.id,
            initial_payment_id=payment2.id,
            amount_at_risk_cents=75000,
            currency="INR",
            failure_category=FailureCategory.TECHNICAL_GATEWAY_TIMEOUT,
            status=RecoveryCaseStatus.WAITING_EXTERNAL,
            next_action_scheduled_at=future_time,
            deadline_at=deadline,
        )
        session.add_all([case_expired, case_future])
        await session.flush()
        case_expired_id = case_expired.id
        case_future_id = case_future.id
        await session.commit()

        # Run scheduled reassessment
        result = await _reassess_scheduled_cases_async(session_factory=async_session)
        assert result["status"] == "success"
        assert result["reassessed_cases_count"] == 1

        # Verify statuses in database using a clean new session
        async with async_session() as verify_session:
            stmt_expired = select(RecoveryCaseModel).where(RecoveryCaseModel.id == case_expired_id)
            updated_expired = (await verify_session.execute(stmt_expired)).scalar_one()
            assert updated_expired.status == RecoveryCaseStatus.DETECTED
            assert updated_expired.next_action_scheduled_at is None

            stmt_future = select(RecoveryCaseModel).where(RecoveryCaseModel.id == case_future_id)
            updated_future = (await verify_session.execute(stmt_future)).scalar_one()
            assert updated_future.status == RecoveryCaseStatus.WAITING_EXTERNAL
            assert updated_future.next_action_scheduled_at is not None

    await engine.dispose()
