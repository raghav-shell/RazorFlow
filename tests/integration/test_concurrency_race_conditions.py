"""Integration tests verifying concurrency, race condition handling, and database idempotency on PostgreSQL."""

import asyncio
import hashlib
import hmac
import json
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from packages.adapters.razorpay.webhooks import parse_razorpay_webhook
from packages.domain.enums import OrderStatus, PaymentStatus
from packages.orchestration.services.case_creation_service import CaseCreationService
from packages.orchestration.services.webhook_ingestion_service import WebhookIngestionService
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.raw_event import RawWebhookEventModel
from packages.persistence.models.recovery_case import RecoveryCaseModel

POSTGRES_TEST_URL = (
    "postgresql+asyncpg://razorflow:razorflow_dev_password@localhost:5432/razorflow_db"
)


@pytest.mark.asyncio
async def test_concurrent_duplicate_webhook_ingestion():
    """
    Simulates 5 concurrent HTTP requests sending the exact same webhook event ID at the exact same millisecond.
    PostgreSQL unique constraint on (merchant_id, event_id) guarantees exactly 1 insert, with 4 returning duplicate_ignored.
    """
    engine = create_async_engine(POSTGRES_TEST_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    merchant_id = uuid.uuid4()
    slug = f"concurrent-{uuid.uuid4().hex[:6]}"
    secret = "whsec_concurrent_123"

    async with session_factory() as session:
        merchant = MerchantModel(id=merchant_id, name="Concurrent Store", slug=slug)
        session.add(merchant)
        await session.flush()
        config = MerchantProviderConfigModel(
            merchant_id=merchant.id,
            provider="RAZORPAY",
            key_id="k",
            key_secret_enc="s",
            webhook_secret_enc=secret,
            is_active=True,
        )
        session.add(config)
        await session.commit()

    payload = {"event": "payment.failed", "created_at": 1700000000}
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
    headers = {"x-razorpay-event-id": f"evt_concurrent_race_{uuid.uuid4().hex[:8]}"}

    async def ingest_one():
        async with session_factory() as session:
            try:
                is_dup, event = await WebhookIngestionService.ingest_razorpay_webhook(
                    session=session,
                    merchant_slug=slug,
                    raw_body_bytes=raw_bytes,
                    signature=sig,
                    headers=headers,
                )
                await session.commit()
                return is_dup
            except Exception as e:
                await session.rollback()
                return f"error: {e}"

    # Fire 5 concurrent ingestion requests
    results = await asyncio.gather(*(ingest_one() for _ in range(5)))

    # Exactly one request must be is_duplicate=False (inserted), the other 4 must be is_duplicate=True
    inserted_count = sum(1 for r in results if r is False)
    duplicate_count = sum(1 for r in results if r is True)

    assert inserted_count == 1
    assert duplicate_count == 4

    # Verify database has exactly 1 raw event row
    async with session_factory() as session:
        stmt = select(RawWebhookEventModel).where(
            RawWebhookEventModel.merchant_id == merchant_id,
            RawWebhookEventModel.event_id == headers["x-razorpay-event-id"],
        )
        events = (await session.execute(stmt)).scalars().all()
        assert len(events) == 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_case_creation_race_condition():
    """
    Simulates multiple background worker threads attempting to create a RecoveryCase for the same order at once.
    Ensures that only 1 active RecoveryCase is created for the order due to row locking and partial unique index.
    """
    engine = create_async_engine(POSTGRES_TEST_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    merchant_id = uuid.uuid4()
    order_id = uuid.uuid4()
    payment_id = uuid.uuid4()

    async with session_factory() as session:
        merchant = MerchantModel(
            id=merchant_id, name="Race Store", slug=f"race-{uuid.uuid4().hex[:6]}"
        )
        session.add(merchant)
        await session.flush()

        order = OrderModel(
            id=order_id,
            merchant_id=merchant_id,
            external_order_id=f"order_race_{uuid.uuid4().hex[:6]}",
            amount_cents=150000,
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        session.add(order)
        await session.flush()

        payment = PaymentModel(
            id=payment_id,
            merchant_id=merchant_id,
            order_id=order_id,
            external_payment_id=f"pay_race_{uuid.uuid4().hex[:6]}",
            amount_cents=150000,
            currency="INR",
            status=PaymentStatus.FAILED,
        )
        session.add(payment)
        await session.commit()

    raw_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment.external_payment_id,
                    "order_id": order.external_order_id,
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
        "created_at": 1700000000,
    }
    parsed = parse_razorpay_webhook(json.dumps(raw_payload).encode("utf-8"), {})

    async def create_case_concurrently():
        async with session_factory() as session:
            try:
                # Reload order and payment in this session
                ord_obj = await session.get(OrderModel, order_id)
                pay_obj = await session.get(PaymentModel, payment_id)
                case, is_new = await CaseCreationService.create_or_update_recovery_case(
                    session=session,
                    merchant_id=merchant_id,
                    order=ord_obj,  # type: ignore[arg-type]
                    payment=pay_obj,  # type: ignore[arg-type]
                    customer=None,
                    payload=parsed,
                    enrichment_context={"test": True},
                )
                await session.commit()
                return str(case.id)
            except Exception as e:
                await session.rollback()
                return f"error: {e}"

    # Fire 3 concurrent creation calls
    case_ids = await asyncio.gather(*(create_case_concurrently() for _ in range(3)))

    # All returned case IDs must be identical
    valid_ids = [c for c in case_ids if not c.startswith("error")]
    assert len(valid_ids) >= 1
    assert len(set(valid_ids)) == 1

    # Verify database has exactly 1 RecoveryCase row for this order
    async with session_factory() as session:
        stmt = select(RecoveryCaseModel).where(RecoveryCaseModel.order_id == order_id)
        cases = (await session.execute(stmt)).scalars().all()
        assert len(cases) == 1

    await engine.dispose()
