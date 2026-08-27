"""Unit tests for Baseline Heuristic Recovery Probability Scorer."""

import uuid
from datetime import datetime, timezone

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType, RecoveryCaseStatus
from packages.domain.scoring.probability_scorer import BaselineHeuristicProbabilityScorer
from packages.domain.value_objects import MonetaryAmount


def create_snapshot(
    failure_category: FailureCategory = FailureCategory.USER_AUTHENTICATION_DROPOFF,
    is_transient: bool = True,
    current_attempts: int = 0,
) -> RecoveryCaseSnapshot:
    now = datetime.now(timezone.utc)
    return RecoveryCaseSnapshot(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        amount_at_risk=MonetaryAmount.from_paise(100000),
        amount_recovered=MonetaryAmount.from_paise(0),
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category=failure_category,
        is_transient=is_transient,
        current_attempt_count=current_attempts,
        max_allowed_attempts=2,
        deadline_at=now,
    )


def test_probability_scorer_bounds_and_effects():
    scorer = BaselineHeuristicProbabilityScorer()
    case = create_snapshot(failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)

    # 1. Base Score for Payment Link
    prob_link = scorer.score(case, ctx, RecoveryActionType.PAYMENT_LINK)
    assert 0.0 <= prob_link.value <= 1.0
    assert prob_link.value >= 0.60

    # 2. DO_NOTHING has low probability
    prob_dn = scorer.score(case, ctx, RecoveryActionType.DO_NOTHING)
    assert prob_dn.value <= 0.10

    # 3. Fraud Risk Block has 0.0 probability across all actions
    case_fraud = create_snapshot(
        failure_category=FailureCategory.FRAUD_RISK_BLOCK, is_transient=False
    )
    prob_fraud = scorer.score(case_fraud, ctx, RecoveryActionType.PAYMENT_LINK)
    assert prob_fraud.value == 0.0

    # 4. VIP customer with successful history increases probability
    ctx_vip = CaseEnrichmentContext(
        customer_id=case.customer_id,
        historical_success_count=5,
        historical_failure_count=0,
        previous_recovery_count=2,
    )
    prob_vip = scorer.score(case, ctx_vip, RecoveryActionType.PAYMENT_LINK)
    assert prob_vip.value > prob_link.value

    # 5. Attempt decay: 2nd attempt has lower probability than 1st
    case_att2 = create_snapshot(current_attempts=2)
    prob_att2 = scorer.score(case_att2, ctx, RecoveryActionType.PAYMENT_LINK)
    assert prob_att2.value < prob_link.value
