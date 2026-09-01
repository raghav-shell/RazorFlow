"""Unit tests for bounded Candidate Generator."""

import uuid
from datetime import datetime, timezone

from packages.domain.candidate_generator import CandidateGenerator
from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType, RecoveryCaseStatus
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.value_objects import MonetaryAmount


def create_snapshot(
    amount_cents: int = 100000,
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
        amount_at_risk=MonetaryAmount.from_paise(amount_cents),
        amount_recovered=MonetaryAmount.from_paise(0),
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category=failure_category,
        is_transient=is_transient,
        current_attempt_count=current_attempts,
        max_allowed_attempts=2,
        deadline_at=now,
    )


def test_candidate_generation_standard_case():
    case = create_snapshot()
    ctx = CaseEnrichmentContext(customer_id=case.customer_id, has_active_payment_link=False)
    policy = MerchantPolicySnapshot()

    candidates = CandidateGenerator.generate_candidates(case, ctx, policy)

    # PAYMENT_LINK, WAIT_AND_REASSESS, DO_NOTHING should be eligible
    # CUSTOMER_REMINDER is NOT eligible because has_active_payment_link=False
    assert RecoveryActionType.PAYMENT_LINK in candidates
    assert RecoveryActionType.CUSTOMER_REMINDER not in candidates
    assert RecoveryActionType.DO_NOTHING in candidates


def test_candidate_generation_with_active_link():
    case = create_snapshot()
    ctx = CaseEnrichmentContext(customer_id=case.customer_id, has_active_payment_link=True)
    policy = MerchantPolicySnapshot()

    candidates = CandidateGenerator.generate_candidates(case, ctx, policy)
    assert RecoveryActionType.CUSTOMER_REMINDER in candidates


def test_candidate_generation_disallowed_actions():
    case = create_snapshot()
    ctx = CaseEnrichmentContext(customer_id=case.customer_id, has_active_payment_link=True)
    # Merchant disallows PAYMENT_LINK
    policy = MerchantPolicySnapshot(disallowed_actions=[RecoveryActionType.PAYMENT_LINK])

    candidates = CandidateGenerator.generate_candidates(case, ctx, policy)
    assert RecoveryActionType.PAYMENT_LINK not in candidates
    assert RecoveryActionType.CUSTOMER_REMINDER in candidates


def test_candidate_generation_fraud_fallback_to_do_nothing():
    case = create_snapshot(failure_category=FailureCategory.FRAUD_RISK_BLOCK, is_transient=False)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    policy = MerchantPolicySnapshot()

    candidates = CandidateGenerator.generate_candidates(case, ctx, policy)
    assert candidates == [RecoveryActionType.DO_NOTHING]
