"""Concurrency and race condition tests for execution and financial verification on PostgreSQL."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from packages.adapters.razorpay.mock_gateway_adapter import MockPaymentGatewayAdapter
from packages.domain.commands import RecoveryCommand
from packages.domain.enums import (
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.orchestration.services.action_orchestrator import (
    ActionOrchestrator,
    OrchestrationResult,
)
from packages.orchestration.services.verification_service import (
    VerificationResult,
    VerificationService,
)
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel

POSTGRES_TEST_URL = (
    "postgresql+asyncpg://razorflow:razorflow_dev_password@localhost:5432/razorflow_db"
)


@pytest.mark.asyncio
async def test_concurrent_command_execution_race():
    """
    Two workers attempt to execute the exact same RecoveryCommand concurrently on PostgreSQL.
    Row-level locking (FOR UPDATE) and unique idempotency keys guarantee exactly ONE attempt record.
    """
    engine = create_async_engine(POSTGRES_TEST_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    case_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    order_id = uuid.uuid4()
    payment_id = uuid.uuid4()

    async with session_factory() as session:
        merchant = MerchantModel(
            id=merchant_id,
            name="Race Store",
            slug=f"race-{uuid.uuid4().hex[:6]}",
            currency="INR",
        )
        session.add(merchant)
        await session.flush()

        order = OrderModel(
            id=order_id,
            merchant_id=merchant.id,
            external_order_id=f"ord_race_{uuid.uuid4().hex[:6]}",
            amount_cents=500000,
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        session.add(order)
        await session.flush()

        payment = PaymentModel(
            id=payment_id,
            merchant_id=merchant.id,
            order_id=order.id,
            external_payment_id=f"pay_init_{uuid.uuid4().hex[:6]}",
            amount_cents=500000,
            currency="INR",
            status=PaymentStatus.FAILED,
        )
        session.add(payment)
        await session.flush()

        case = RecoveryCaseModel(
            id=case_id,
            merchant_id=merchant.id,
            order_id=order.id,
            initial_payment_id=payment.id,
            amount_at_risk_cents=500000,
            currency="INR",
            status=RecoveryCaseStatus.APPROVED,
            deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
        )
        session.add(case)
        await session.commit()
        deadline_at = case.deadline_at

    cmd = RecoveryCommand.create(
        case_id=case_id,
        merchant_id=merchant_id,
        order_id=order_id,
        action_type=RecoveryActionType.PAYMENT_LINK,
        attempt_number=1,
        amount_cents=500000,
        currency="INR",
        deadline_at=deadline_at,
    )

    mock_gateway = MockPaymentGatewayAdapter()

    async def _worker_exec():
        async with session_factory() as worker_sess:
            try:
                res = await ActionOrchestrator.execute_command(
                    session=worker_sess,
                    command=cmd,
                    gateway=mock_gateway,
                )
                await worker_sess.commit()
                return res
            except Exception as e:
                await worker_sess.rollback()
                return f"error: {e}"

    # Launch 3 concurrent workers
    raw_results = await asyncio.gather(*(_worker_exec() for _ in range(3)))

    # Invariant: At least one worker succeeded cleanly
    successes = [r for r in raw_results if isinstance(r, OrchestrationResult)]
    assert len(successes) >= 1
    assert successes[0].idempotency_key == cmd.idempotency_key

    # Total attempts in database for this case must be exactly 1
    async with session_factory() as check_sess:
        attempts = (
            (
                await check_sess.execute(
                    select(RecoveryAttemptModel).where(RecoveryAttemptModel.case_id == case_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(attempts) == 1
        assert attempts[0].idempotency_key == cmd.idempotency_key

    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_verification_race():
    """
    Two concurrent verification tasks (e.g. duplicate webhooks) attempt to verify the same case on PostgreSQL.
    Out-of-order & idempotency protections ensure exactly ONE outcome is established.
    """
    engine = create_async_engine(POSTGRES_TEST_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    case_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    order_id = uuid.uuid4()
    payment_id = uuid.uuid4()

    async with session_factory() as session:
        merchant = MerchantModel(
            id=merchant_id,
            name="Verif Race",
            slug=f"vr-{uuid.uuid4().hex[:6]}",
            currency="INR",
        )
        session.add(merchant)
        await session.flush()

        order = OrderModel(
            id=order_id,
            merchant_id=merchant.id,
            external_order_id=f"ord_vr_{uuid.uuid4().hex[:6]}",
            amount_cents=400000,
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        session.add(order)
        await session.flush()

        payment = PaymentModel(
            id=payment_id,
            merchant_id=merchant.id,
            order_id=order.id,
            external_payment_id=f"pay_vr_{uuid.uuid4().hex[:6]}",
            amount_cents=400000,
            currency="INR",
            status=PaymentStatus.CAPTURED,
        )
        session.add(payment)
        await session.flush()

        case = RecoveryCaseModel(
            id=case_id,
            merchant_id=merchant.id,
            order_id=order.id,
            initial_payment_id=payment.id,
            amount_at_risk_cents=400000,
            currency="INR",
            status=RecoveryCaseStatus.WAITING_EXTERNAL,
            deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
        )
        session.add(case)
        await session.commit()

    async def _verify_task():
        async with session_factory() as v_sess:
            try:
                v_case = await v_sess.get(RecoveryCaseModel, case_id)
                v_pay = await v_sess.get(PaymentModel, payment_id)
                res = await VerificationService.verify_and_recover_case(
                    session=v_sess,
                    case=v_case,
                    settling_payment=v_pay,
                    verification_source="CONCURRENT_RACE",
                )
                await v_sess.commit()
                return res
            except Exception as e:
                await v_sess.rollback()
                return f"error: {e}"

    raw_results = await asyncio.gather(*(_verify_task() for _ in range(3)))

    # Invariant: At least one worker verified the case
    successes = [r for r in raw_results if isinstance(r, VerificationResult)]
    assert len(successes) >= 1
    assert successes[0].is_verified is True
    assert successes[0].recovered_amount_cents == 400000

    # Exactly ONE outcome created in the database
    async with session_factory() as check_sess:
        outcomes = (
            (
                await check_sess.execute(
                    select(RecoveryOutcomeModel).where(RecoveryOutcomeModel.case_id == case_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(outcomes) == 1
        assert outcomes[0].amount_recovered_cents == 400000
        assert outcomes[0].is_successful is True

    await engine.dispose()
