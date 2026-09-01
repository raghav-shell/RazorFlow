"""Unit tests for Financial Verification Service and calculations."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.enums import (
    PaymentStatus,
    RecoveryActionType,
    RecoveryAttemptStatus,
    RecoveryCaseStatus,
)
from packages.orchestration.services.verification_service import VerificationService
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_verification_calculates_exact_integer_net_recovery(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Verif Mart", slug=f"vf-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_{uuid.uuid4().hex[:6]}",
        amount_cents=1000000,  # ₹10,000.00
        currency="INR",
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=1000000,
        amount_recovered_cents=0,
        currency="INR",
        status=RecoveryCaseStatus.WAITING_EXTERNAL,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    # Attempt with PAYMENT_LINK (cost = 200 paise = ₹2.00)
    attempt = RecoveryAttemptModel(
        case_id=case.id,
        merchant_id=merchant.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        idempotency_key="cmd_plink_1",
        status=RecoveryAttemptStatus.ACKNOWLEDGED,
        gateway_reference_id="plink_123",
    )
    async_db_session.add(attempt)
    await async_db_session.flush()

    # Settling payment captured: 1,000,000 paise (₹10,000.00)
    payment = PaymentModel(
        merchant_id=merchant.id,
        order_id=order.id,
        external_payment_id="pay_settled_1",
        amount_cents=1000000,
        currency="INR",
        status=PaymentStatus.CAPTURED,
    )
    async_db_session.add(payment)
    await async_db_session.flush()

    result = await VerificationService.verify_and_recover_case(
        session=async_db_session,
        case=case,
        settling_payment=payment,
        verification_source="TEST_UNIT",
        gateway_reference_id="plink_123",
    )

    # 1. Verification succeeds
    assert result.is_verified is True
    assert result.case_status == RecoveryCaseStatus.RECOVERED
    assert result.recovered_amount_cents == 1000000
    # Net recovery = 1,000,000 - 200 = 999,800 paise (₹9,998.00)
    assert result.net_recovery_cents == 999800
    assert isinstance(result.net_recovery_cents, int)
    assert case.status == RecoveryCaseStatus.RECOVERED
    assert attempt.status == RecoveryAttemptStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_verification_rejects_non_captured_payment(async_db_session: AsyncSession):
    case = RecoveryCaseModel(
        merchant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=500000,
        currency="INR",
        status=RecoveryCaseStatus.WAITING_EXTERNAL,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    payment_failed = PaymentModel(
        merchant_id=case.merchant_id,
        order_id=case.order_id,
        external_payment_id="pay_fail",
        amount_cents=500000,
        currency="INR",
        status=PaymentStatus.FAILED,
    )

    result = await VerificationService.verify_and_recover_case(
        session=async_db_session,
        case=case,
        settling_payment=payment_failed,
        verification_source="TEST_UNIT",
    )

    assert result.is_verified is False
    assert "not CAPTURED" in (result.failure_reason or "")
    assert case.status == RecoveryCaseStatus.WAITING_EXTERNAL
