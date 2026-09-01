"""Unit tests for pure domain Recovery Strategies."""

import uuid
from datetime import datetime, timezone

from packages.domain.entities import CaseEnrichmentContext, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType, RecoveryCaseStatus
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.strategies import (
    CustomerReminderStrategy,
    DoNothingStrategy,
    HumanEscalationStrategy,
    PaymentLinkStrategy,
    WaitAndReassessStrategy,
    get_recovery_strategy,
)
from packages.domain.value_objects import MonetaryAmount


def create_sample_case_snapshot(
    amount_cents: int = 100000,
    failure_category: FailureCategory = FailureCategory.USER_AUTHENTICATION_DROPOFF,
    is_transient: bool = True,
    current_attempt_count: int = 0,
    max_allowed_attempts: int = 2,
    metadata_json: dict | None = None,
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
        diagnosis_reasoning="Test reasoning",
        current_attempt_count=current_attempt_count,
        max_allowed_attempts=max_allowed_attempts,
        deadline_at=now,
        metadata=metadata_json or {},
    )


def test_strategy_registry_lookup():
    strat = get_recovery_strategy(RecoveryActionType.PAYMENT_LINK)
    assert isinstance(strat, PaymentLinkStrategy)
    assert strat.action_type == RecoveryActionType.PAYMENT_LINK


def test_payment_link_strategy_eligibility():
    strat = PaymentLinkStrategy()
    case = create_sample_case_snapshot(amount_cents=250000)
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot()

    eval_result = strat.evaluate(case, ctx, pol)
    assert eval_result.is_eligible is True
    assert eval_result.intervention_cost.amount_in_cents == 200  # ₹2.00
    assert eval_result.ineligibility_reason is None

    # Ineligible when attempts exhausted
    case_exhausted = create_sample_case_snapshot(current_attempt_count=2, max_allowed_attempts=2)
    eval_exhausted = strat.evaluate(case_exhausted, ctx, pol)
    assert eval_exhausted.is_eligible is False
    assert "Max recovery attempts" in (eval_exhausted.ineligibility_reason or "")

    # Ineligible for fraud risk block
    case_fraud = create_sample_case_snapshot(failure_category=FailureCategory.FRAUD_RISK_BLOCK)
    eval_fraud = strat.evaluate(case_fraud, ctx, pol)
    assert eval_fraud.is_eligible is False


def test_customer_reminder_strategy_requires_active_link():
    strat = CustomerReminderStrategy()
    pol = MerchantPolicySnapshot()

    # Case WITHOUT active link -> Ineligible
    case_no_link = create_sample_case_snapshot()
    ctx_no_link = CaseEnrichmentContext(
        customer_id=case_no_link.customer_id, has_active_payment_link=False
    )
    eval_no_link = strat.evaluate(case_no_link, ctx_no_link, pol)
    assert eval_no_link.is_eligible is False
    assert "No active payment link exists" in (eval_no_link.ineligibility_reason or "")

    # Case WITH active link -> Eligible
    ctx_with_link = CaseEnrichmentContext(
        customer_id=case_no_link.customer_id, has_active_payment_link=True
    )
    eval_with_link = strat.evaluate(case_no_link, ctx_with_link, pol)
    assert eval_with_link.is_eligible is True
    assert eval_with_link.intervention_cost.amount_in_cents == 150  # ₹1.50
    assert eval_with_link.risk_penalty.amount_in_cents == 100  # ₹1.00


def test_wait_and_reassess_strategy():
    strat = WaitAndReassessStrategy()
    pol = MerchantPolicySnapshot()

    case_outage = create_sample_case_snapshot(
        failure_category=FailureCategory.BANK_SYSTEM_OUTAGE, is_transient=True
    )
    ctx = CaseEnrichmentContext(customer_id=case_outage.customer_id)
    eval_outage = strat.evaluate(case_outage, ctx, pol)

    assert eval_outage.is_eligible is True
    assert eval_outage.intervention_cost.amount_in_cents == 0
    assert eval_outage.risk_penalty.amount_in_cents == 0


def test_human_escalation_strategy_high_value():
    strat = HumanEscalationStrategy()
    pol = MerchantPolicySnapshot(high_value_escalation_threshold_cents=5000000)

    # Standard value ₹1,000.00 -> Ineligible
    case_std = create_sample_case_snapshot(amount_cents=100000)
    ctx_std = CaseEnrichmentContext(customer_id=case_std.customer_id)
    eval_std = strat.evaluate(case_std, ctx_std, pol)
    assert eval_std.is_eligible is False

    # High value ₹60,000.00 -> Eligible
    case_high = create_sample_case_snapshot(amount_cents=6000000)
    eval_high = strat.evaluate(case_high, ctx_std, pol)
    assert eval_high.is_eligible is True
    assert eval_high.intervention_cost.amount_in_cents == 10000  # ₹100.00


def test_do_nothing_strategy():
    strat = DoNothingStrategy()
    case = create_sample_case_snapshot()
    ctx = CaseEnrichmentContext(customer_id=case.customer_id)
    pol = MerchantPolicySnapshot()

    eval_dn = strat.evaluate(case, ctx, pol)
    assert eval_dn.is_eligible is True
    assert eval_dn.intervention_cost.amount_in_cents == 0
    assert eval_dn.risk_penalty.amount_in_cents == 0
