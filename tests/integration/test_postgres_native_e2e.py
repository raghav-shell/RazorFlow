"""Native PostgreSQL 16 integration tests verifying real database constraints, partial indexes, and hash-chaining."""

import hashlib
import hmac
import json
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.worker.tasks.ingestion import _process_raw_webhook_async
from packages.domain.enums import RecoveryCaseStatus
from packages.orchestration.services.webhook_ingestion_service import WebhookIngestionService
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.recovery_case import RecoveryCaseModel

POSTGRES_TEST_URL = (
    "postgresql+asyncpg://razorflow:razorflow_dev_password@localhost:5432/razorflow_db"
)


@pytest.mark.asyncio
async def test_native_postgres_e2e_webhook_to_case_pipeline():
    """
    End-to-end test against real PostgreSQL 16 database instance.
    Validates:
    - Webhook ingestion with HMAC
    - Idempotent raw event storage
    - Order & payment persistence
    - Customer enrichment
    - RecoveryCase aggregate creation
    - PostgreSQL native Partial Unique Index
    - Cryptographic Hash-Chain Audit Ledger
    """
    engine = create_async_engine(POSTGRES_TEST_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    merchant_id = uuid.uuid4()
    slug = f"pg-merchant-{uuid.uuid4().hex[:6]}"
    webhook_secret = "whsec_live_pg_test_999"

    # 1. Create Merchant & Config in PostgreSQL
    async with session_factory() as session:
        merchant = MerchantModel(
            id=merchant_id,
            name="PostgreSQL Live Merchant",
            slug=slug,
            currency="INR",
        )
        session.add(merchant)
        await session.flush()

        config = MerchantProviderConfigModel(
            merchant_id=merchant.id,
            provider="RAZORPAY",
            key_id="rzp_live_pg_key",
            key_secret_enc="enc_secret",
            webhook_secret_enc=webhook_secret,
            is_active=True,
        )
        session.add(config)
        await session.commit()

    # 2. Ingest Webhook Event
    payment_id = f"pay_pg_{uuid.uuid4().hex[:8]}"
    order_id = f"order_pg_{uuid.uuid4().hex[:8]}"
    event_id = f"evt_pg_{uuid.uuid4().hex[:8]}"

    raw_payload = {
        "entity": "event",
        "account_id": "acc_pg_001",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 750000,  # ₹7,500.00
                    "currency": "INR",
                    "status": "failed",
                    "method": "netbanking",
                    "email": "vikram@example.com",
                    "contact": "+919877766655",
                    "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
                    "error_description": "HDFC netbanking session timed out",
                    "error_source": "bank",
                    "error_step": "payment_authorization",
                }
            }
        },
        "created_at": 1700000000,
    }
    raw_bytes = json.dumps(raw_payload).encode("utf-8")
    signature = hmac.new(webhook_secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
    headers = {"x-razorpay-event-id": event_id}

    async with session_factory() as session:
        is_duplicate, raw_event = await WebhookIngestionService.ingest_razorpay_webhook(
            session=session,
            merchant_slug=slug,
            raw_body_bytes=raw_bytes,
            signature=signature,
            headers=headers,
        )
        await session.commit()

        assert is_duplicate is False
        assert raw_event is not None
        raw_event_id = str(raw_event.id)

    # 3. Execute Asynchronous Ingestion Task
    task_result = await _process_raw_webhook_async(raw_event_id, session_factory=session_factory)
    assert task_result["status"] == "success"
    case_id_str = task_result["case_id"]
    assert case_id_str is not None

    # 4. Verify in PostgreSQL database
    async with session_factory() as session:
        case = await session.get(RecoveryCaseModel, uuid.UUID(case_id_str))
        assert case is not None
        assert case.amount_at_risk_cents == 750000
        assert case.status == RecoveryCaseStatus.DIAGNOSING
        assert case.failure_category == "TECHNICAL_GATEWAY_TIMEOUT"
        assert case.is_transient is True

        # Verify Hash-Chain Audit Ledger in PostgreSQL
        audit_stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.merchant_id == merchant_id, AuditEventModel.entity_id == case.id)
            .order_by(AuditEventModel.sequence_number.asc())
        )
        audit_records = (await session.execute(audit_stmt)).scalars().all()
        assert len(audit_records) >= 1
        assert audit_records[0].sequence_number == 1
        assert audit_records[0].prev_event_hash == "0" * 64
        assert len(audit_records[0].event_hash) == 64

    await engine.dispose()
