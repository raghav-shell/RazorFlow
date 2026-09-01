"""Integration tests for AI Decision Service with Mocked Gemini Provider and Fallback."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.ai.mock_adapter import MockStrategyAIAdapter
from packages.domain.entities import CaseEnrichmentContext
from packages.domain.enums import (
    OrderStatus,
    PaymentStatus,
    PolicyVerdict,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.orchestration.services.ai_decision_service import AIDecisionService
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import RecoveryDecisionModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_ai_decision_service_standard_approval(async_db_session: AsyncSession):
    merchant = MerchantModel(name="AI Store", slug=f"ai-{uuid.uuid4().hex[:6]}", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_ai_{uuid.uuid4().hex[:6]}",
        amount_cents=450000,  # ₹4,500.00
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    payment = PaymentModel(
        merchant_id=merchant.id,
        order_id=order.id,
        external_payment_id=f"pay_ai_{uuid.uuid4().hex[:6]}",
        amount_cents=450000,
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
        amount_at_risk_cents=450000,
        currency="INR",
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category="TECHNICAL_GATEWAY_TIMEOUT",
        is_transient=True,
        diagnosis_reasoning="Bank gateway timeout",
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    ctx = CaseEnrichmentContext(customer_id=case.customer_id, historical_success_count=3)
    policy = MerchantPolicySnapshot(max_allowed_attempts=2)

    # Use Mock AI recommending PAYMENT_LINK
    ai_mock = MockStrategyAIAdapter(
        force_action=RecoveryActionType.PAYMENT_LINK,
        force_confidence=0.92,
        force_diagnosis="Transient timeout occurred during peak banking hours.",
        force_rationale="Interactive payment link allows the customer to retry conveniently.",
    )

    result = await AIDecisionService.evaluate_with_ai(
        session=async_db_session,
        case=case,
        context=ctx,
        policy=policy,
        ai_client=ai_mock,
    )
    await async_db_session.commit()

    # 1. Verify Pipeline Results
    assert result.case_id == case.id
    assert result.ai_recommendation.recommended_action == RecoveryActionType.PAYMENT_LINK
    assert result.ai_recommendation.confidence_score == 0.92
    assert result.ai_metadata.is_fallback is False
    assert result.policy_evaluation.verdict == PolicyVerdict.APPROVED
    assert result.authorized_command is not None
    assert result.authorized_command.action_type == RecoveryActionType.PAYMENT_LINK

    # 2. Verify Case State Machine: DIAGNOSING -> APPROVED
    assert case.status == RecoveryCaseStatus.APPROVED
    assert case.last_ai_confidence == 0.92
    assert case.diagnosis_reasoning == "Transient timeout occurred during peak banking hours."

    # 3. Verify Database Decision Record
    decision = await async_db_session.get(RecoveryDecisionModel, result.decision_record_id)
    assert decision is not None
    assert decision.ai_recommended_action == RecoveryActionType.PAYMENT_LINK
    assert decision.ai_confidence == 0.92
    assert "ai_metadata" in decision.ai_raw_response
    assert decision.ai_raw_response["ai_metadata"]["is_fallback"] is False

    # 4. Verify Cryptographic Hash Chain Audit Event
    audit_stmt = select(AuditEventModel).where(
        AuditEventModel.merchant_id == merchant.id,
        AuditEventModel.entity_id == decision.id,
    )
    audit = (await async_db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None
    assert audit.action == "AI_RECOVERY_DECISION_EVALUATED"
    assert audit.actor_type == "AI_AGENT"
    assert len(audit.event_hash) == 64


@pytest.mark.asyncio
async def test_ai_decision_service_timeout_fallback_to_erv(async_db_session: AsyncSession):
    merchant = MerchantModel(
        name="Fallback Mart", slug=f"fb-{uuid.uuid4().hex[:6]}", currency="INR"
    )
    async_db_session.add(merchant)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant.id,
        external_order_id=f"ord_fb_{uuid.uuid4().hex[:6]}",
        amount_cents=200000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    payment = PaymentModel(
        merchant_id=merchant.id,
        order_id=order.id,
        external_payment_id=f"pay_fb_{uuid.uuid4().hex[:6]}",
        amount_cents=200000,
        currency="INR",
        status=PaymentStatus.FAILED,
    )
    async_db_session.add(payment)
    await async_db_session.flush()

    case = RecoveryCaseModel(
        merchant_id=merchant.id,
        order_id=order.id,
        initial_payment_id=payment.id,
        amount_at_risk_cents=200000,
        currency="INR",
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category="USER_AUTHENTICATION_DROPOFF",
        is_transient=True,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    async_db_session.add(case)
    await async_db_session.flush()

    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    policy = MerchantPolicySnapshot()

    # Mock AI that times out!
    ai_timeout_mock = MockStrategyAIAdapter(should_timeout=True)

    result = await AIDecisionService.evaluate_with_ai(
        session=async_db_session,
        case=case,
        context=ctx,
        policy=policy,
        ai_client=ai_timeout_mock,
    )
    await async_db_session.commit()

    # Invariant: AI Timeout must seamlessly fallback to deterministic ERV recommendation
    assert result.ai_metadata.is_fallback is True
    assert "TimeoutError" in (result.ai_metadata.fallback_reason or "")
    assert result.ai_recommendation.recommended_action == result.deterministic_recommendation
    assert result.policy_evaluation.verdict == PolicyVerdict.APPROVED
    assert case.status == RecoveryCaseStatus.APPROVED
