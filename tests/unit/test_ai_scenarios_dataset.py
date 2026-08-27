"""Evaluation test dataset covering all 14 AI Recovery Strategy scenarios."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from packages.adapters.ai.mock_adapter import MockStrategyAIAdapter
from packages.domain.ai.context_builder import AIContextBuilder
from packages.domain.candidate_generator import CandidateGenerator
from packages.domain.entities import CaseEnrichmentContext, CustomerSnapshot, RecoveryCaseSnapshot
from packages.domain.enums import (
    FailureCategory,
    PolicyVerdict,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.engine import PolicyEngine
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.value_objects import MonetaryAmount, RiskScore


def build_scenario_fixture(
    amount_cents: int = 200000,
    failure_category: FailureCategory = FailureCategory.USER_AUTHENTICATION_DROPOFF,
    is_transient: bool = True,
    current_attempts: int = 0,
    has_active_link: bool = False,
    disallowed_actions: list[RecoveryActionType] | None = None,
    high_value_threshold: int = 5000000,
) -> tuple[RecoveryCaseSnapshot, CaseEnrichmentContext, MerchantPolicySnapshot]:
    now = datetime.now(timezone.utc)
    cust_id = uuid.uuid4()
    customer = CustomerSnapshot(
        id=cust_id,
        merchant_id=uuid.uuid4(),
        external_customer_id="cust_eval",
        email="eval@example.com",
        phone="+919876543210",
        name="Eval User",
        risk_score=RiskScore(0.3),
    )
    case = RecoveryCaseSnapshot(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        customer_id=cust_id,
        amount_at_risk=MonetaryAmount.from_paise(amount_cents),
        amount_recovered=MonetaryAmount.from_paise(0),
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category=failure_category,
        is_transient=is_transient,
        current_attempt_count=current_attempts,
        max_allowed_attempts=2,
        deadline_at=now + timedelta(hours=72),
    )
    ctx = CaseEnrichmentContext(customer=customer, has_active_payment_link=has_active_link)
    policy = MerchantPolicySnapshot(
        disallowed_actions=disallowed_actions or [],
        high_value_escalation_threshold_cents=high_value_threshold,
    )
    return case, ctx, policy


@pytest.mark.asyncio
async def test_scenario_1_temporary_bank_outage():
    case, ctx, pol = build_scenario_fixture(
        failure_category=FailureCategory.BANK_SYSTEM_OUTAGE, is_transient=True
    )
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert RecoveryActionType.WAIT_AND_REASSESS in cands


@pytest.mark.asyncio
async def test_scenario_2_gateway_timeout():
    case, ctx, pol = build_scenario_fixture(
        failure_category=FailureCategory.TECHNICAL_GATEWAY_TIMEOUT, is_transient=True
    )
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert RecoveryActionType.PAYMENT_LINK in cands
    assert RecoveryActionType.WAIT_AND_REASSESS in cands


@pytest.mark.asyncio
async def test_scenario_3_insufficient_funds():
    case, ctx, pol = build_scenario_fixture(
        failure_category=FailureCategory.INSUFFICIENT_FUNDS, is_transient=True
    )
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert RecoveryActionType.PAYMENT_LINK in cands


@pytest.mark.asyncio
async def test_scenario_4_permanent_card_decline():
    case, ctx, pol = build_scenario_fixture(
        failure_category=FailureCategory.PERMANENT_INSTRUMENT_DECLINE, is_transient=False
    )
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    # WAIT_AND_REASSESS is ineligible for permanent decline
    assert RecoveryActionType.WAIT_AND_REASSESS not in cands


@pytest.mark.asyncio
async def test_scenario_5_fraud_block():
    case, ctx, pol = build_scenario_fixture(
        failure_category=FailureCategory.FRAUD_RISK_BLOCK, is_transient=False
    )
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert cands == [RecoveryActionType.DO_NOTHING]


@pytest.mark.asyncio
async def test_scenario_6_high_value_transaction():
    case, ctx, pol = build_scenario_fixture(amount_cents=8000000, high_value_threshold=5000000)
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert RecoveryActionType.HUMAN_ESCALATION in cands

    # Policy escalation test
    eval_res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert eval_res.verdict == PolicyVerdict.ESCALATED
    assert eval_res.authorized_action == RecoveryActionType.HUMAN_ESCALATION


@pytest.mark.asyncio
async def test_scenario_7_repeated_failures():
    case, ctx, pol = build_scenario_fixture(current_attempts=2)
    # Attempts exhausted -> Policy modifies to DO_NOTHING
    eval_res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert eval_res.verdict == PolicyVerdict.MODIFIED
    assert eval_res.authorized_action == RecoveryActionType.DO_NOTHING


@pytest.mark.asyncio
async def test_scenario_8_active_payment_link():
    case, ctx, pol = build_scenario_fixture(has_active_link=True)
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert RecoveryActionType.CUSTOMER_REMINDER in cands


@pytest.mark.asyncio
async def test_scenario_9_no_active_payment_link():
    case, ctx, pol = build_scenario_fixture(has_active_link=False)
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    assert RecoveryActionType.CUSTOMER_REMINDER not in cands


@pytest.mark.asyncio
async def test_scenario_10_ai_timeout_fallback():
    ai = MockStrategyAIAdapter(should_timeout=True)
    case, ctx, pol = build_scenario_fixture()
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    ai_ctx = AIContextBuilder.build_context(case, ctx, cands, [], pol)

    with pytest.raises(TimeoutError):
        await ai.recommend_strategy(ai_ctx)


@pytest.mark.asyncio
async def test_scenario_11_malformed_ai_response():
    ai = MockStrategyAIAdapter(should_fail_error=ValueError("Malformed JSON response"))
    case, ctx, pol = build_scenario_fixture()
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    ai_ctx = AIContextBuilder.build_context(case, ctx, cands, [], pol)

    with pytest.raises(ValueError):
        await ai.recommend_strategy(ai_ctx)


@pytest.mark.asyncio
async def test_scenario_12_invalid_action_returned():
    ai = MockStrategyAIAdapter(invalid_action_name="RETRY_CARD_DIRECT")
    case, ctx, pol = build_scenario_fixture()
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    ai_ctx = AIContextBuilder.build_context(case, ctx, cands, [], pol)

    with pytest.raises(ValueError):
        await ai.recommend_strategy(ai_ctx)


@pytest.mark.asyncio
async def test_scenario_13_conflicting_ai_recommendation_vs_erv():
    # Gemini recommends WAIT_AND_REASSESS while ERV recommends PAYMENT_LINK
    case, ctx, pol = build_scenario_fixture()
    cands = CandidateGenerator.generate_candidates(case, ctx, pol)
    ai = MockStrategyAIAdapter(force_action=RecoveryActionType.WAIT_AND_REASSESS)
    ai_ctx = AIContextBuilder.build_context(case, ctx, cands, [], pol)

    rec, meta = await ai.recommend_strategy(ai_ctx)
    assert rec.recommended_action == RecoveryActionType.WAIT_AND_REASSESS
    # Policy authorizes AI recommendation if it clears guardrails
    eval_res = PolicyEngine.evaluate(rec.recommended_action, case, ctx, pol)
    assert eval_res.authorized_action == RecoveryActionType.WAIT_AND_REASSESS


@pytest.mark.asyncio
async def test_scenario_14_policy_disallowed_ai_recommendation():
    # Merchant disallows PAYMENT_LINK, but AI recommends PAYMENT_LINK
    case, ctx, pol = build_scenario_fixture(disallowed_actions=[RecoveryActionType.PAYMENT_LINK])
    eval_res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    # Policy modifies or rejects AI action
    assert eval_res.verdict == PolicyVerdict.MODIFIED
    assert eval_res.authorized_action != RecoveryActionType.PAYMENT_LINK
