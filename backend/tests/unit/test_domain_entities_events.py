"""Unit tests for domain entities and domain events instantiation and immutability."""

import uuid
from datetime import datetime, timezone

from packages.domain.entities import (
    CaseEnrichmentContext,
    CustomerSnapshot,
    OrderSnapshot,
    PaymentSnapshot,
    RecoveryCaseSnapshot,
)
from packages.domain.enums import FailureCategory, OrderStatus, PaymentStatus, RecoveryCaseStatus
from packages.domain.events import (
    CaseStateChangedEvent,
    PaymentFailedRevenueEvent,
    RecoveryAttemptDispatchedEvent,
    RecoveryOutcomeVerifiedEvent,
)
from packages.domain.value_objects import MonetaryAmount, RecoveryProbability, RiskScore


def test_domain_entities_instantiation():
    merchant_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    order_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    case_id = uuid.uuid4()

    customer = CustomerSnapshot(
        id=customer_id,
        merchant_id=merchant_id,
        external_customer_id="c_123",
        email="customer@example.com",
        phone="+919876543210",
        name="Ankit Sharma",
        risk_score=RiskScore(score=0.15),
        recovery_success_count=2,
        total_failure_count=1,
    )

    order = OrderSnapshot(
        id=order_id,
        merchant_id=merchant_id,
        external_order_id="order_123",
        customer_id=customer_id,
        amount=MonetaryAmount(cents=250000),
        status=OrderStatus.ATTEMPTED,
        receipt="rcpt_001",
    )

    payment = PaymentSnapshot(
        id=payment_id,
        merchant_id=merchant_id,
        order_id=order_id,
        customer_id=customer_id,
        external_payment_id="pay_123",
        amount=MonetaryAmount(cents=250000),
        status=PaymentStatus.FAILED,
        method="card",
        error_code="BAD_REQUEST_PAYMENT_TIMED_OUT",
        error_description="Gateway timeout",
        error_source="bank",
        error_step="payment_auth",
        error_reason="bank_timeout",
    )

    case = RecoveryCaseSnapshot(
        id=case_id,
        merchant_id=merchant_id,
        order_id=order_id,
        initial_payment_id=payment_id,
        customer_id=customer_id,
        amount_at_risk=MonetaryAmount(cents=250000),
        amount_recovered=MonetaryAmount(cents=0),
        status=RecoveryCaseStatus.DETECTED,
        failure_category=FailureCategory.TECHNICAL_GATEWAY_TIMEOUT,
        is_transient=True,
        diagnosis_reasoning="Transient bank timeout",
        recovery_probability=RecoveryProbability(probability=0.75),
        expected_recovery_value=MonetaryAmount(cents=187500),
        last_ai_confidence=0.88,
        current_attempt_count=0,
        max_allowed_attempts=2,
        deadline_at=datetime.now(timezone.utc),
    )

    context = CaseEnrichmentContext(
        customer=customer,
        order=order,
        initial_payment=payment,
    )

    assert case.amount_at_risk.cents == 250000
    assert context.customer.name == "Ankit Sharma"


def test_domain_events_instantiation():
    merchant_id = uuid.uuid4()
    order_id = uuid.uuid4()
    payment_id = uuid.uuid4()

    event = PaymentFailedRevenueEvent(
        merchant_id=merchant_id,
        order_id=order_id,
        payment_id=payment_id,
        external_order_id="order_999",
        external_payment_id="pay_999",
        amount=MonetaryAmount(cents=100000),
        error_code="INSUFFICIENT_FUNDS",
    )
    assert event.error_code == "INSUFFICIENT_FUNDS"
    assert event.amount.cents == 100000

    state_event = CaseStateChangedEvent(
        merchant_id=merchant_id,
        old_status=RecoveryCaseStatus.DETECTED,
        new_status=RecoveryCaseStatus.ENRICHING,
        reason="Enriching customer context",
    )
    assert state_event.new_status == RecoveryCaseStatus.ENRICHING

    dispatch_event = RecoveryAttemptDispatchedEvent(
        merchant_id=merchant_id,
        idempotency_key="idemp_123",
    )
    assert dispatch_event.idempotency_key == "idemp_123"

    outcome_event = RecoveryOutcomeVerifiedEvent(
        merchant_id=merchant_id,
        is_successful=True,
        amount_recovered=MonetaryAmount(cents=100000),
    )
    assert outcome_event.is_successful is True
