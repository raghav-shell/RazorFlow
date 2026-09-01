"""Integration tests for Action Orchestrator and idempotent execution."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
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
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_action_orchestrator_e2e_execution(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Orch Store", slug=f"orch-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_orch_{uuid.uuid4().hex[:6]}",
        amount_cents=300000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=uuid.uuid4(),
        amount_at_risk_cents=300000,
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
        amount_cents=300000,
        currency="INR",
        deadline_at=case.deadline_at,
    )

    mock_gateway = MockPaymentGatewayAdapter()

    # 1. Execute Command via ActionOrchestrator
    res = await ActionOrchestrator.execute_command(
        session=async_db_session,
        command=cmd,
        gateway=mock_gateway,
    )
    await async_db_session.commit()

    # 2. Verify Execution Output
    assert res.case_id == case.id
    assert res.is_duplicate_execution is False
    assert res.attempt_status == RecoveryAttemptStatus.ACKNOWLEDGED
    assert res.case_status == RecoveryCaseStatus.WAITING_EXTERNAL
    assert res.gateway_reference_id is not None
    assert res.gateway_reference_id.startswith("plink_")

    # 3. Verify Database State
    reloaded_case = await async_db_session.get(RecoveryCaseModel, case.id)
    assert reloaded_case.status == RecoveryCaseStatus.WAITING_EXTERNAL
    assert reloaded_case.current_attempt_count == 1

    attempt = await async_db_session.get(RecoveryAttemptModel, res.attempt_id)
    assert attempt is not None
    assert attempt.status == RecoveryAttemptStatus.ACKNOWLEDGED
    assert attempt.gateway_reference_id == res.gateway_reference_id

    # 4. Verify Cryptographic Audit Trail
    audit_stmt = (
        select(AuditEventModel)
        .where(
            AuditEventModel.merchant_id == merchant.id,
            AuditEventModel.entity_id == attempt.id,
        )
        .order_by(AuditEventModel.sequence_number.asc())
    )
    audits = (await async_db_session.execute(audit_stmt)).scalars().all()
    assert len(audits) >= 2
    actions = [a.action for a in audits]
    assert "ATTEMPT_CREATED" in actions
    assert "GATEWAY_ACCEPTED" in actions

    # 5. Idempotency Hit Test: Re-executing exact same command returns duplicate without re-creating
    dup_res = await ActionOrchestrator.execute_command(
        session=async_db_session,
        command=cmd,
        gateway=mock_gateway,
    )
    assert dup_res.is_duplicate_execution is True
    assert dup_res.attempt_id == res.attempt_id
