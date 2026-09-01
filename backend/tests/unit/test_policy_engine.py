"""Unit tests for deterministic Policy Engine and all 10 hard guardrails."""

import uuid
from datetime import datetime, timedelta, timezone

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import (
    FailureCategory,
    PolicyVerdict,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.engine import PolicyEngine
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.scoring.erv_calculator import ERVResult
from packages.domain.value_objects import MonetaryAmount, RecoveryProbability


def create_snapshot(
    amount_cents: int = 100000,
    status: RecoveryCaseStatus = RecoveryCaseStatus.DIAGNOSING,
    failure_category: FailureCategory = FailureCategory.USER_AUTHENTICATION_DROPOFF,
    is_transient: bool = True,
    current_attempts: int = 0,
    max_attempts: int = 2,
    deadline_at: datetime | None = None,
    last_attempt_at: datetime | None = None,
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
        status=status,
        failure_category=failure_category,
        is_transient=is_transient,
        current_attempt_count=current_attempts,
        max_allowed_attempts=max_attempts,
        deadline_at=deadline_at or (now + timedelta(hours=72)),
        last_attempt_at=last_attempt_at,
    )


def test_guardrail_1_terminal_case_rejected():
    case = create_snapshot(status=RecoveryCaseStatus.RECOVERED)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot()

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert res.verdict == PolicyVerdict.REJECTED
    assert res.authorized_action == RecoveryActionType.DO_NOTHING
    assert res.rule_code == "CASE_ALREADY_TERMINAL"


def test_guardrail_2_expired_deadline_modified():
    now = datetime.now(timezone.utc)
    expired_time = now - timedelta(minutes=5)
    case = create_snapshot(deadline_at=expired_time)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot()

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol, now=now)
    assert res.verdict == PolicyVerdict.MODIFIED
    assert res.authorized_action == RecoveryActionType.DO_NOTHING
    assert res.rule_code == "DEADLINE_EXPIRED"


def test_guardrail_3_max_attempts_exceeded():
    case = create_snapshot(current_attempts=2, max_attempts=2)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot(max_allowed_attempts=2)

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert res.verdict == PolicyVerdict.MODIFIED
    assert res.authorized_action == RecoveryActionType.DO_NOTHING
    assert res.rule_code == "MAX_ATTEMPTS_EXCEEDED"


def test_guardrail_4_active_cooldown_modified_to_wait():
    now = datetime.now(timezone.utc)
    recent_attempt = now - timedelta(minutes=10)
    case = create_snapshot(last_attempt_at=recent_attempt)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot(cooldown_period_minutes=30)

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol, now=now)
    assert res.verdict == PolicyVerdict.MODIFIED
    assert res.authorized_action == RecoveryActionType.WAIT_AND_REASSESS
    assert res.rule_code == "COOLDOWN_ACTIVE"
    assert res.reassessment_delay_seconds is not None
    assert res.reassessment_delay_seconds > 0


def test_guardrail_5_fraud_risk_guard_rejected():
    case = create_snapshot(failure_category=FailureCategory.FRAUD_RISK_BLOCK, is_transient=False)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot()

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert res.verdict == PolicyVerdict.REJECTED
    assert res.authorized_action == RecoveryActionType.DO_NOTHING
    assert res.rule_code == "FRAUD_RISK_GUARD"


def test_guardrail_6_reminder_without_active_link_modified_to_link():
    case = create_snapshot()
    ctx = CaseEnrichmentContext(customer_id=case.customer_id, has_active_payment_link=False)
    pol = MerchantPolicySnapshot()

    res = PolicyEngine.evaluate(RecoveryActionType.CUSTOMER_REMINDER, case, ctx, pol)
    assert res.verdict == PolicyVerdict.MODIFIED
    assert res.authorized_action == RecoveryActionType.PAYMENT_LINK
    assert res.rule_code == "NO_ACTIVE_PAYMENT_LINK"


def test_guardrail_7_high_value_escalation():
    case = create_snapshot(amount_cents=7500000)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot(high_value_escalation_threshold_cents=5000000)

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert res.verdict == PolicyVerdict.ESCALATED
    assert res.authorized_action == RecoveryActionType.HUMAN_ESCALATION
    assert res.rule_code == "HIGH_VALUE_THRESHOLD_EXCEEDED"


def test_guardrail_8_merchant_disallowed_action():
    case = create_snapshot(amount_cents=200000)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot(disallowed_actions=[RecoveryActionType.PAYMENT_LINK])

    erv_rankings = [
        ERVResult(
            action=RecoveryActionType.PAYMENT_LINK,
            recovery_probability=RecoveryProbability.from_float(0.70),
            amount_at_risk_cents=200000,
            gross_expected_recovery_cents=140000,
            intervention_cost_cents=200,
            risk_penalty_cents=50,
            expected_net_recovery_value_cents=139750,
            rationale="Disallowed",
        ),
        ERVResult(
            action=RecoveryActionType.WAIT_AND_REASSESS,
            recovery_probability=RecoveryProbability.from_float(0.50),
            amount_at_risk_cents=200000,
            gross_expected_recovery_cents=100000,
            intervention_cost_cents=0,
            risk_penalty_cents=0,
            expected_net_recovery_value_cents=100000,
            rationale="Fallback",
        ),
    ]

    res = PolicyEngine.evaluate(
        RecoveryActionType.PAYMENT_LINK, case, ctx, pol, erv_rankings=erv_rankings
    )
    assert res.verdict == PolicyVerdict.MODIFIED
    assert res.authorized_action == RecoveryActionType.WAIT_AND_REASSESS
    assert res.rule_code == "ACTION_DISALLOWED_BY_MERCHANT"


def test_policy_always_wins_over_erv():
    case = create_snapshot(amount_cents=10000000, current_attempts=2, max_attempts=2)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot(max_allowed_attempts=2)

    res = PolicyEngine.evaluate(RecoveryActionType.PAYMENT_LINK, case, ctx, pol)
    assert res.verdict == PolicyVerdict.MODIFIED
    assert res.authorized_action == RecoveryActionType.DO_NOTHING
    assert res.rule_code == "MAX_ATTEMPTS_EXCEEDED"
