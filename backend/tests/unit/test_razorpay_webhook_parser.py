"""Unit tests for Razorpay webhook verification and payload parsing."""

import json

from packages.adapters.razorpay.webhooks import (
    classify_razorpay_failure,
    parse_razorpay_webhook,
    verify_razorpay_signature,
)
from packages.domain.enums import FailureCategory


def test_verify_razorpay_signature_valid():
    secret = "rzp_webhook_secret_999"
    payload = b'{"event":"payment.failed"}'

    import hashlib
    import hmac

    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_razorpay_signature(payload, valid_sig, secret) is True
    assert verify_razorpay_signature(payload, "invalid_sig", secret) is False
    assert verify_razorpay_signature(b"other", valid_sig, secret) is False


def test_classify_razorpay_failure_taxonomies():
    # Timeout -> TECHNICAL_GATEWAY_TIMEOUT (transient=True)
    cat, is_transient = classify_razorpay_failure(
        "BAD_REQUEST_PAYMENT_TIMED_OUT", "bank", "payment_auth", "timeout"
    )
    assert cat == FailureCategory.TECHNICAL_GATEWAY_TIMEOUT
    assert is_transient is True

    # Bank outage -> BANK_SYSTEM_OUTAGE (transient=True)
    cat, is_transient = classify_razorpay_failure("BANK_DOWNTIME", "bank", "step", "reason")
    assert cat == FailureCategory.BANK_SYSTEM_OUTAGE
    assert is_transient is True

    # Auth dropoff -> USER_AUTHENTICATION_DROPOFF (transient=True)
    cat, is_transient = classify_razorpay_failure(
        "OTP_FAILED", "customer", "payment_authentication", "user_abandoned"
    )
    assert cat == FailureCategory.USER_AUTHENTICATION_DROPOFF
    assert is_transient is True

    # Insufficient funds -> INSUFFICIENT_FUNDS (transient=True)
    cat, is_transient = classify_razorpay_failure(
        "BAD_REQUEST_PAYMENT_ACCOUNT_INSUFFICIENT_BALANCE", "customer", "auth", "no_balance"
    )
    assert cat == FailureCategory.INSUFFICIENT_FUNDS
    assert is_transient is True

    # Fraud block -> FRAUD_RISK_BLOCK (transient=False)
    cat, is_transient = classify_razorpay_failure(
        "RISK_BLOCKED", "gateway", "auth", "fraud_detected"
    )
    assert cat == FailureCategory.FRAUD_RISK_BLOCK
    assert is_transient is False

    # Expired card -> PERMANENT_INSTRUMENT_DECLINE (transient=False)
    cat, is_transient = classify_razorpay_failure(
        "EXPIRED_CARD", "customer", "step", "card_expired"
    )
    assert cat == FailureCategory.PERMANENT_INSTRUMENT_DECLINE
    assert is_transient is False


def test_parse_razorpay_webhook_payload():
    raw_payload = {
        "entity": "event",
        "account_id": "acc_test_123",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_001",
                    "order_id": "order_test_001",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "email": "gaurav@example.com",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
                    "error_description": "Payment attempt timed out at issuing bank",
                    "error_source": "bank",
                    "error_step": "payment_authorization",
                    "error_reason": "payment_timed_out",
                }
            }
        },
        "created_at": 1700000000,
    }
    raw_bytes = json.dumps(raw_payload).encode("utf-8")
    headers = {"x-razorpay-event-id": "evt_official_999"}

    parsed = parse_razorpay_webhook(raw_bytes, headers)

    assert parsed.event_id == "evt_official_999"
    assert parsed.event_type == "payment.failed"
    assert parsed.external_payment_id == "pay_test_001"
    assert parsed.external_order_id == "order_test_001"
    assert parsed.amount_cents == 250000
    assert parsed.customer_email == "gaurav@example.com"
    assert parsed.failure_category == FailureCategory.TECHNICAL_GATEWAY_TIMEOUT
    assert parsed.is_transient_failure is True
