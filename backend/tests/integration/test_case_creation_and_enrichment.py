"""Integration tests for RecoveryCase creation, customer enrichment, and audit hash-chaining."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.worker.tasks.ingestion import _process_raw_webhook_async
from packages.domain.enums import RecoveryCaseStatus
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.raw_event import RawWebhookEventModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_case_creation_and_enrichment_flow(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Electronics Mart", slug=f"mart-{uuid.uuid4().hex[:6]}")
    async_db_session.add(merchant)
    await async_db_session.flush()

    raw_payload = {
        "entity": "event",
        "account_id": "acc_001",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_case_001",
                    "order_id": "order_case_001",
                    "amount": 499900,  # ₹4,999.00
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "email": "ankit@example.com",
                    "contact": "+919811122233",
                    "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
                    "error_description": "UPI PSP Timeout",
                    "error_source": "bank",
                    "error_step": "payment_authorization",
                }
            }
        },
        "created_at": 1700000000,
    }

    # 1. Create Raw Webhook Event in DB
    raw_event = RawWebhookEventModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        event_id="evt_case_test_001",
        event_type="payment.failed",
        payload=raw_payload,
        signature="sig_dummy",
        processed=False,
    )
    async_db_session.add(raw_event)
    await async_db_session.flush()

    # 2. Run background processor
    result = await _process_raw_webhook_async(str(raw_event.id), session=async_db_session)
    assert result["status"] == "success"
    assert result["case_id"] is not None

    # 3. Verify RecoveryCase created in database
    case_id = uuid.UUID(result["case_id"])
    case = await async_db_session.get(RecoveryCaseModel, case_id)
    assert case is not None
    assert case.amount_at_risk_cents == 499900
    assert case.currency == "INR"
    assert case.status == RecoveryCaseStatus.DIAGNOSING
    assert case.failure_category == "TECHNICAL_GATEWAY_TIMEOUT"
    assert case.is_transient is True
    assert case.current_attempt_count == 0
    assert case.max_allowed_attempts == 2

    # 4. Verify Customer Enrichment data stored in metadata
    enrichment = case.metadata_json.get("enrichment_context", {})
    assert enrichment.get("has_customer_profile") is True
    assert enrichment.get("customer_risk_tier") in (
        "NEW_CUSTOMER",
        "STANDARD",
        "LOW_RISK_VIP",
        "ELEVATED_RISK",
    )
    assert "masked_customer_name" in enrichment

    # 5. Verify Cryptographic Hash-Chain Audit Event
    audit_stmt = (
        select(AuditEventModel)
        .where(AuditEventModel.merchant_id == merchant.id, AuditEventModel.entity_id == case.id)
        .order_by(AuditEventModel.sequence_number.asc())
    )
    audit_events = (await async_db_session.execute(audit_stmt)).scalars().all()
    assert len(audit_events) >= 1
    genesis_audit = audit_events[0]
    assert genesis_audit.sequence_number == 1
    assert genesis_audit.prev_event_hash == "0" * 64
    assert len(genesis_audit.event_hash) == 64
    assert genesis_audit.action == "RECOVERY_CASE_CREATED"


@pytest.mark.asyncio
async def test_repeated_failure_updates_active_case_without_duplication(
    async_db_session: AsyncSession,
):
    merchant = MerchantModel(name="Gadget Store", slug=f"gadget-{uuid.uuid4().hex[:6]}")
    async_db_session.add(merchant)
    await async_db_session.flush()

    # Event 1: First payment failure on order_repeat_001
    payload1 = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_repeat_1",
                    "order_id": "order_repeat_001",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
        "created_at": 1700000000,
    }
    raw_event1 = RawWebhookEventModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        event_id="evt_rep_1",
        event_type="payment.failed",
        payload=payload1,
        signature="sig",
        processed=False,
    )
    async_db_session.add(raw_event1)
    await async_db_session.flush()

    res1 = await _process_raw_webhook_async(str(raw_event1.id), session=async_db_session)
    case_id_1 = res1["case_id"]

    # Event 2: Second payment failure on SAME order_repeat_001
    payload2 = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_repeat_2",
                    "order_id": "order_repeat_001",
                    "amount": 200000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
        "created_at": 1700000100,
    }
    raw_event2 = RawWebhookEventModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        event_id="evt_rep_2",
        event_type="payment.failed",
        payload=payload2,
        signature="sig",
        processed=False,
    )
    async_db_session.add(raw_event2)
    await async_db_session.flush()

    res2 = await _process_raw_webhook_async(str(raw_event2.id), session=async_db_session)
    case_id_2 = res2["case_id"]

    # Invariant: Must update the SAME RecoveryCase, NOT create a second case!
    assert case_id_1 == case_id_2

    # Verify total cases count for this order is exactly 1
    stmt = select(RecoveryCaseModel).where(RecoveryCaseModel.merchant_id == merchant.id)
    cases = (await async_db_session.execute(stmt)).scalars().all()
    assert len(cases) == 1
