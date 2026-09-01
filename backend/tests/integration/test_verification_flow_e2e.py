"""Integration tests for end-to-end Financial Verification and Webhook/Polling Reconciliation."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.razorpay.mock_gateway_adapter import MockPaymentGatewayAdapter
from packages.adapters.razorpay.webhooks import ParsedRazorpayPaymentPayload
from packages.domain.enums import (
    FailureCategory,
    OrderStatus,
    RecoveryActionType,
    RecoveryAttemptStatus,
    RecoveryCaseStatus,
)
from packages.orchestration.services.verification_service import VerificationService
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel


@pytest.mark.asyncio
async def test_webhook_driven_financial_verification(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Verif Flow", slug=f"vf-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"order_{uuid.uuid4().hex[:8]}",
        amount_cents=500000,  # ₹5,000.00
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=500000,
        amount_recovered_cents=0,
        currency="INR",
        status=RecoveryCaseStatus.WAITING_EXTERNAL,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    attempt = RecoveryAttemptModel(
        case_id=case.id,
        merchant_id=merchant.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        idempotency_key="cmd_verif_1",
        status=RecoveryAttemptStatus.ACKNOWLEDGED,
        gateway_reference_id="plink_success_123",
    )
    async_db_session.add(attempt)
    await async_db_session.flush()

    # 1. Incoming Canonical Webhook event (payment.captured)
    event = ParsedRazorpayPaymentPayload(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        event_type="payment.captured",
        account_id=None,
        external_payment_id=f"pay_{uuid.uuid4().hex[:8]}",
        external_order_id=order.external_order_id,
        amount_cents=500000,
        currency="INR",
        status="captured",
        method="upi",
        description="Payment captured via recovery link",
        customer_email="payer@example.com",
        customer_contact="+919876543210",
        customer_name="Payer User",
        error_code=None,
        error_description=None,
        error_source=None,
        error_step=None,
        error_reason=None,
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        is_transient_failure=False,
        created_at_timestamp=datetime.now(timezone.utc),
        raw_payload={"payload": {"payment_link": {"entity": {"id": "plink_success_123"}}}},
    )

    result = await VerificationService.verify_from_webhook_event(
        session=async_db_session,
        event=event,
        merchant_id=merchant.id,
    )
    await async_db_session.commit()

    # 2. Verify Case Transition: WAITING_EXTERNAL -> RECOVERED
    assert result is not None
    assert result.is_verified is True
    assert result.case_status == RecoveryCaseStatus.RECOVERED
    assert result.recovered_amount_cents == 500000
    # Net recovery = 500,000 - 200 (payment link cost) = 499,800 paise
    assert result.net_recovery_cents == 499800

    reloaded_case = await async_db_session.get(RecoveryCaseModel, case.id)
    assert reloaded_case.status == RecoveryCaseStatus.RECOVERED
    assert reloaded_case.amount_recovered_cents == 500000

    # 3. Verify RecoveryOutcomeModel
    outcome = await async_db_session.get(RecoveryOutcomeModel, result.outcome_id)
    assert outcome is not None
    assert outcome.is_successful is True
    assert outcome.amount_recovered_cents == 500000
    assert outcome.net_recovery_cents == 499800
    assert outcome.verification_source == "WEBHOOK_EVENT"


@pytest.mark.asyncio
async def test_polling_driven_reconciliation(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Poll Store", slug=f"ps-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"order_poll_{uuid.uuid4().hex[:8]}",
        amount_cents=250000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=250000,
        amount_recovered_cents=0,
        currency="INR",
        status=RecoveryCaseStatus.WAITING_EXTERNAL,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    # Link created on attempt
    attempt = RecoveryAttemptModel(
        case_id=case.id,
        merchant_id=merchant.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        idempotency_key="cmd_poll_1",
        status=RecoveryAttemptStatus.ACKNOWLEDGED,
        gateway_reference_id="plink_paid_999",
    )
    async_db_session.add(attempt)
    await async_db_session.flush()

    # Mock gateway returning paid status for this link
    mock_gateway = MockPaymentGatewayAdapter(
        force_link_status="paid", force_payment_status="captured"
    )
    mock_gateway.created_links["plink_paid_999"] = {
        "id": "plink_paid_999",
        "short_url": "https://rzp.io/i/test",
        "status": "paid",
        "amount": 250000,
        "currency": "INR",
    }

    # Execute Polling Reconciliation
    result = await VerificationService.poll_and_reconcile_case(
        session=async_db_session,
        case_id=case.id,
        gateway=mock_gateway,
    )
    await async_db_session.commit()

    assert result.is_verified is True
    assert result.case_status == RecoveryCaseStatus.RECOVERED
    assert result.recovered_amount_cents == 250000
    assert result.verification_source == "GATEWAY_POLL"
