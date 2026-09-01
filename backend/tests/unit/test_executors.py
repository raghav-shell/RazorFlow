"""Unit tests for all pure Action Executors."""

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
from packages.orchestration.executors import (
    HumanEscalationExecutor,
    PaymentLinkExecutor,
    PaymentLinkReminderExecutor,
    WaitAndReassessExecutor,
    get_executor_for_action,
)
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


def test_executor_registry_lookup():
    assert isinstance(get_executor_for_action(RecoveryActionType.PAYMENT_LINK), PaymentLinkExecutor)
    assert isinstance(
        get_executor_for_action(RecoveryActionType.CUSTOMER_REMINDER), PaymentLinkReminderExecutor
    )
    assert isinstance(
        get_executor_for_action(RecoveryActionType.WAIT_AND_REASSESS), WaitAndReassessExecutor
    )
    assert isinstance(
        get_executor_for_action(RecoveryActionType.HUMAN_ESCALATION), HumanEscalationExecutor
    )


@pytest.mark.asyncio
async def test_payment_link_executor_success(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Store", slug=f"st-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_{uuid.uuid4().hex[:6]}",
        amount_cents=150000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=150000,
        currency="INR",
        status=RecoveryCaseStatus.EXECUTING,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    attempt = RecoveryAttemptModel(
        case_id=case.id,
        merchant_id=merchant.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        idempotency_key=f"cmd_{case.id}_1_PAYMENT_LINK",
        status=RecoveryAttemptStatus.DISPATCHED,
    )
    async_db_session.add(attempt)
    await async_db_session.flush()

    cmd = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=merchant.id,
        order_id=order.id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        attempt_number=1,
        amount_cents=150000,
        currency="INR",
        deadline_at=case.deadline_at,
    )

    mock_gateway = MockPaymentGatewayAdapter()
    executor = PaymentLinkExecutor()

    res = await executor.execute(
        session=async_db_session,
        command=cmd,
        case=case,
        attempt=attempt,
        gateway=mock_gateway,
    )

    assert res.is_success is True
    assert res.attempt_status == RecoveryAttemptStatus.ACKNOWLEDGED
    assert res.target_case_status == RecoveryCaseStatus.WAITING_EXTERNAL
    assert res.gateway_reference_id is not None
    assert res.gateway_reference_id.startswith("plink_")


@pytest.mark.asyncio
async def test_wait_and_reassess_executor(async_db_session: AsyncSession):
    case = RecoveryCaseModel(
        merchant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=100000,
        currency="INR",
        status=RecoveryCaseStatus.EXECUTING,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    attempt = RecoveryAttemptModel(
        case_id=case.id,
        merchant_id=case.merchant_id,
        action_type=RecoveryActionType.WAIT_AND_REASSESS,
        idempotency_key="cmd_wait_1",
    )
    cmd = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=case.merchant_id,
        order_id=case.order_id,
        action_type=RecoveryActionType.WAIT_AND_REASSESS,
        attempt_number=1,
        amount_cents=100000,
        currency="INR",
        deadline_at=case.deadline_at,
        payload={"reassessment_delay_seconds": 900},
    )

    executor = WaitAndReassessExecutor()
    res = await executor.execute(
        session=async_db_session,
        command=cmd,
        case=case,
        attempt=attempt,
        gateway=MockPaymentGatewayAdapter(),
    )

    assert res.is_success is True
    assert res.attempt_status == RecoveryAttemptStatus.SUCCEEDED
    assert res.target_case_status == RecoveryCaseStatus.WAITING_EXTERNAL
    assert case.next_action_scheduled_at is not None


@pytest.mark.asyncio
async def test_human_escalation_executor(async_db_session: AsyncSession):
    case = RecoveryCaseModel(
        merchant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=10000000,
        currency="INR",
        status=RecoveryCaseStatus.EXECUTING,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    attempt = RecoveryAttemptModel(
        case_id=case.id,
        merchant_id=case.merchant_id,
        action_type=RecoveryActionType.HUMAN_ESCALATION,
        idempotency_key="cmd_esc_1",
    )
    cmd = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=case.merchant_id,
        order_id=case.order_id,
        action_type=RecoveryActionType.HUMAN_ESCALATION,
        attempt_number=1,
        amount_cents=10000000,
        currency="INR",
        deadline_at=case.deadline_at,
    )

    executor = HumanEscalationExecutor()
    res = await executor.execute(
        session=async_db_session,
        command=cmd,
        case=case,
        attempt=attempt,
        gateway=MockPaymentGatewayAdapter(),
    )

    assert res.is_success is True
    assert res.attempt_status == RecoveryAttemptStatus.SUCCEEDED
    assert res.target_case_status == RecoveryCaseStatus.ESCALATED
