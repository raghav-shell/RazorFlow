"""Unit tests for Expected Recovery Value (ERV) Calculator and Ranker."""

import uuid
from datetime import datetime, timezone

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType, RecoveryCaseStatus
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.scoring.erv_calculator import ERVCalculator, ERVResult
from packages.domain.scoring.erv_ranker import ERVRanker
from packages.domain.value_objects import MonetaryAmount, RecoveryProbability


def test_erv_calculator_exact_integer_math():
    case = RecoveryCaseSnapshot(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        amount_at_risk=MonetaryAmount.from_paise(1000000),  # ₹10,000.00
        amount_recovered=MonetaryAmount.from_paise(0),
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
        is_transient=True,
        diagnosis_reasoning=None,
        recovery_probability=None,
        expected_recovery_value=None,
        last_ai_confidence=None,
        current_attempt_count=0,
        max_allowed_attempts=2,
        deadline_at=datetime.now(timezone.utc),
    )
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    policy = MerchantPolicySnapshot()

    # Probability = 0.70
    # Gross = int(0.70 * 1,000,000) = 700,000 paise (₹7,000.00)
    # PaymentLink cost = 200 paise, risk penalty = 50 paise
    # Net ERV = 700,000 - 200 - 50 = 699,750 paise (₹6,997.50)
    prob = RecoveryProbability.from_float(0.70)
    result = ERVCalculator.calculate_erv(RecoveryActionType.PAYMENT_LINK, case, ctx, prob, policy)

    assert result.gross_expected_recovery_cents == 700000
    assert result.intervention_cost_cents == 200
    assert result.risk_penalty_cents == 50
    assert result.expected_net_recovery_value_cents == 699750
    assert isinstance(result.expected_net_recovery_value_cents, int)


def test_erv_ranker_deterministic_sorting_and_tie_breaking():
    r1 = ERVResult(
        action=RecoveryActionType.PAYMENT_LINK,
        recovery_probability=RecoveryProbability.from_float(0.70),
        amount_at_risk_cents=100000,
        gross_expected_recovery_cents=70000,
        intervention_cost_cents=200,
        risk_penalty_cents=50,
        expected_net_recovery_value_cents=69750,
        rationale="P1",
    )
    r2 = ERVResult(
        action=RecoveryActionType.WAIT_AND_REASSESS,
        recovery_probability=RecoveryProbability.from_float(0.50),
        amount_at_risk_cents=100000,
        gross_expected_recovery_cents=50000,
        intervention_cost_cents=0,
        risk_penalty_cents=0,
        expected_net_recovery_value_cents=50000,
        rationale="P2",
    )
    r3 = ERVResult(
        action=RecoveryActionType.DO_NOTHING,
        recovery_probability=RecoveryProbability.from_float(0.05),
        amount_at_risk_cents=100000,
        gross_expected_recovery_cents=5000,
        intervention_cost_cents=0,
        risk_penalty_cents=0,
        expected_net_recovery_value_cents=5000,
        rationale="P3",
    )

    ranked = ERVRanker.rank_candidates([r3, r1, r2])

    assert ranked[0].action == RecoveryActionType.PAYMENT_LINK
    assert ranked[1].action == RecoveryActionType.WAIT_AND_REASSESS
    assert ranked[2].action == RecoveryActionType.DO_NOTHING


def test_erv_ranker_tie_breaker_by_cost():
    r_expensive = ERVResult(
        action=RecoveryActionType.HUMAN_ESCALATION,
        recovery_probability=RecoveryProbability.from_float(0.20),
        amount_at_risk_cents=100000,
        gross_expected_recovery_cents=20000,
        intervention_cost_cents=10000,
        risk_penalty_cents=0,
        expected_net_recovery_value_cents=10000,
        rationale="High cost",
    )
    r_cheap = ERVResult(
        action=RecoveryActionType.WAIT_AND_REASSESS,
        recovery_probability=RecoveryProbability.from_float(0.10),
        amount_at_risk_cents=100000,
        gross_expected_recovery_cents=10000,
        intervention_cost_cents=0,
        risk_penalty_cents=0,
        expected_net_recovery_value_cents=10000,
        rationale="Zero cost",
    )

    ranked = ERVRanker.rank_candidates([r_cheap, r_expensive])
    assert ranked[0].action == RecoveryActionType.HUMAN_ESCALATION
