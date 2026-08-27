"""Integration tests for the complete deterministic decision pipeline."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.entities import CaseEnrichmentContext
from packages.domain.enums import (
    OrderStatus,
    PaymentStatus,
    PolicyVerdict,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.orchestration.services.decision_service import DecisionService
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import RecoveryDecisionModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_decision_pipeline_standard_approval(async_db_session: AsyncSession):
    merchant = MerchantModel(
        name="Decision Mart", slug=f"dec-{uuid.uuid4().hex[:6]}", currency="INR"
    )
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_{uuid.uuid4().hex[:6]}",
        amount_cents=350000,  # ₹3,500.00
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    payment = PaymentModel(
        merchant_id=merchant.id,
        order_id=order.id,
        external_payment_id=f"pay_{uuid.uuid4().hex[:6]}",
        amount_cents=350000,
        currency="INR",
        status=PaymentStatus.FAILED,
        error_code="BAD_REQUEST_PAYMENT_TIMED_OUT",
        error_source="bank",
        error_step="payment_authorization",
    )
    async_db_session.add(payment)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=payment.id,
        amount_at_risk_cents=350000,
        currency="INR",
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category="TECHNICAL_GATEWAY_TIMEOUT",
        is_transient=True,
        diagnosis_reasoning="Bank gateway timeout",
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    ctx = CaseEnrichmentContext(customer_id=case.customer_id, historical_success_count=2)
    policy = MerchantPolicySnapshot(max_allowed_attempts=2)

    # Execute Decision Pipeline
    result = await DecisionService.evaluate_case_decision(
        session=async_db_session,
        case=case,
        context=ctx,
        policy=policy,
    )
    await async_db_session.commit()

    # 1. Verify Pipeline Results
    assert result.case_id == case.id
    assert len(result.eligible_candidates) >= 1
    assert result.policy_evaluation.verdict == PolicyVerdict.APPROVED
    assert result.authorized_command is not None
    assert result.authorized_command.action_type == result.policy_evaluation.authorized_action
    assert result.authorized_command.amount_at_risk_cents == 350000
    assert result.authorized_command.idempotency_key.startswith(f"cmd_{case.id}_1_")

    # 2. Verify Case State Transition: DIAGNOSING -> APPROVED
    assert case.status == RecoveryCaseStatus.APPROVED
    assert case.recovery_probability is not None
    assert case.expected_recovery_value_cents is not None

    # 3. Verify Decision Record in Database
    decision = await async_db_session.get(RecoveryDecisionModel, result.decision_record_id)
    assert decision is not None
    assert decision.policy_verdict == PolicyVerdict.APPROVED
    assert "erv_table" in decision.ai_raw_response

    # 4. Verify Cryptographic Hash-Chain Audit Event
    audit_stmt = select(AuditEventModel).where(
        AuditEventModel.merchant_id == merchant.id,
        AuditEventModel.entity_id == decision.id,
    )
    audit = (await async_db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.action == "RECOVERY_DECISION_EVALUATED"
    assert len(audit.event_hash) == 64


@pytest.mark.asyncio
async def test_decision_pipeline_high_value_escalation(async_db_session: AsyncSession):
    merchant = MerchantModel(
        name="Luxury Store", slug=f"lux-{uuid.uuid4().hex[:6]}", currency="INR"
    )
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_lux_{uuid.uuid4().hex[:6]}",
        amount_cents=10000000,  # ₹100,000.00
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    payment = PaymentModel(
        merchant_id=merchant.id,
        order_id=order.id,
        external_payment_id=f"pay_lux_{uuid.uuid4().hex[:6]}",
        amount_cents=10000000,
        currency="INR",
        status=PaymentStatus.FAILED,
    )
    async_db_session.add(payment)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=payment.id,
        amount_at_risk_cents=10000000,
        currency="INR",
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category="USER_AUTHENTICATION_DROPOFF",
        is_transient=True,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    # High-value escalation threshold = ₹50,000.00 (5,000,000 paise)
    policy = MerchantPolicySnapshot(high_value_escalation_threshold_cents=5000000)

    result = await DecisionService.evaluate_case_decision(
        session=async_db_session,
        case=case,
        context=ctx,
        policy=policy,
    )
    await async_db_session.commit()

    # Invariant: Must authorize HUMAN_ESCALATION
    assert result.policy_evaluation.authorized_action == RecoveryActionType.HUMAN_ESCALATION
    assert result.authorized_command is not None
    assert result.authorized_command.action_type == RecoveryActionType.HUMAN_ESCALATION
    assert result.authorized_command.amount_at_risk_cents == 10000000
