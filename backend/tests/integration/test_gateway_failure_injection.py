"""Failure injection tests simulating gateway outages, timeouts, rate limits, and 500 errors."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.razorpay.mock_gateway_adapter import MockPaymentGatewayAdapter
from packages.domain.commands import RecoveryCommand
from packages.domain.enums import (
    OrderStatus,
    RecoveryActionType,
    RecoveryAttemptStatus,
    RecoveryCaseStatus,
)
from packages.orchestration.services.action_orchestrator import ActionOrchestrator
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_failure_injection_gateway_timeout(async_db_session: AsyncSession):
    merchant = MerchantModel(
        name="Timeout Store", slug=f"to-{uuid.uuid4().hex[:6]}", currency="INR"
    )
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_to_{uuid.uuid4().hex[:6]}",
        amount_cents=100000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=100000,
        currency="INR",
        status=RecoveryCaseStatus.APPROVED,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    cmd = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=merchant.id,
        order_id=order.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        attempt_number=1,
        amount_cents=100000,
        currency="INR",
        deadline_at=case.deadline_at,
    )

    # Injected Mock Gateway with Timeout
    timeout_gateway = MockPaymentGatewayAdapter(should_timeout=True)

    res = await ActionOrchestrator.execute_command(
        session=async_db_session,
        command=cmd,
        gateway=timeout_gateway,
    )
    await async_db_session.commit()

    # Invariant: System handles timeout gracefully without crash
    assert res.attempt_status == RecoveryAttemptStatus.FAILED
    assert "Timeout" in (res.error_message or "")
    attempt = await async_db_session.get(RecoveryAttemptModel, res.attempt_id)
    assert attempt.status == RecoveryAttemptStatus.FAILED


@pytest.mark.asyncio
async def test_failure_injection_gateway_500_error(async_db_session: AsyncSession):
    merchant = MerchantModel(name="500 Store", slug=f"err-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_500_{uuid.uuid4().hex[:6]}",
        amount_cents=200000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=200000,
        currency="INR",
        status=RecoveryCaseStatus.APPROVED,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    cmd = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=merchant.id,
        order_id=order.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        attempt_number=1,
        amount_cents=200000,
        currency="INR",
        deadline_at=case.deadline_at,
    )

    gateway_500 = MockPaymentGatewayAdapter(
        should_fail_500=True, custom_error_message="Bank Gateway 500"
    )

    res = await ActionOrchestrator.execute_command(
        session=async_db_session,
        command=cmd,
        gateway=gateway_500,
    )
    await async_db_session.commit()

    assert res.attempt_status == RecoveryAttemptStatus.FAILED
    assert "GATEWAY_INTERNAL_ERROR" in (res.error_message or "")


@pytest.mark.asyncio
async def test_failure_injection_gateway_429_rate_limit(async_db_session: AsyncSession):
    merchant = MerchantModel(name="429 Store", slug=f"rl-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_429_{uuid.uuid4().hex[:6]}",
        amount_cents=200000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=200000,
        currency="INR",
        status=RecoveryCaseStatus.APPROVED,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    cmd = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=merchant.id,
        order_id=order.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        attempt_number=1,
        amount_cents=200000,
        currency="INR",
        deadline_at=case.deadline_at,
    )

    gateway_429 = MockPaymentGatewayAdapter(should_fail_429=True)

    res = await ActionOrchestrator.execute_command(
        session=async_db_session,
        command=cmd,
        gateway=gateway_429,
    )
    await async_db_session.commit()

    assert res.attempt_status == RecoveryAttemptStatus.FAILED
    assert "RATE_LIMIT_EXCEEDED" in (res.error_message or "")
