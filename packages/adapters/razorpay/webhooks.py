"""Razorpay Webhook verification, payload parsing, and failure taxonomy mapping."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from packages.common.crypto import verify_hmac_sha256
from packages.domain.enums import FailureCategory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedRazorpayPaymentPayload:
    """Normalized data extracted directly from a Razorpay payment webhook."""

    event_id: str
    event_type: str
    account_id: Optional[str]
    external_payment_id: str
    external_order_id: Optional[str]
    amount_cents: int
    currency: str
    status: str
    method: Optional[str]
    description: Optional[str]
    customer_email: Optional[str]
    customer_contact: Optional[str]
    customer_name: Optional[str]
    error_code: Optional[str]
    error_description: Optional[str]
    error_source: Optional[str]
    error_step: Optional[str]
    error_reason: Optional[str]
    failure_category: FailureCategory
    is_transient_failure: bool
    created_at_timestamp: datetime
    raw_payload: Dict[str, Any]


def verify_razorpay_signature(raw_body_bytes: bytes, signature: str, webhook_secret: str) -> bool:
    """
    Verifies Razorpay HMAC-SHA256 signature against the exact raw HTTP request body bytes.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not signature or not webhook_secret or not raw_body_bytes:
        return False
    return verify_hmac_sha256(
        payload_bytes=raw_body_bytes,
        secret=webhook_secret,
        received_signature=signature.strip(),
    )


def classify_razorpay_failure(
    error_code: Optional[str],
    error_source: Optional[str],
    error_step: Optional[str],
    error_reason: Optional[str],
) -> tuple[FailureCategory, bool]:
    """
    Deterministically classifies Razorpay payment failure diagnostics into domain FailureCategory
    and determines whether the failure is transient (recoverable) or permanent.
    """
    code = (error_code or "").upper()
    source = (error_source or "").lower()
    step = (error_step or "").lower()
    reason = (error_reason or "").lower()

    # 1. Technical Gateway / Network Timeouts (Transient)
    if (
        "TIMED_OUT" in code
        or "TIMEOUT" in reason
        or "GATEWAY_ERROR" in code
        or code == "SERVER_ERROR"
    ):
        return FailureCategory.TECHNICAL_GATEWAY_TIMEOUT, True

    # 2. Bank System / Issuer Downtime (Transient)
    if source == "bank" and ("DOWNTIME" in code or "UNAVAILABLE" in code or "OFFLINE" in reason):
        return FailureCategory.BANK_SYSTEM_OUTAGE, True

    # 3. User Drop-off / OTP / Authentication Abandonment (Transient/Recoverable via link)
    if (
        "AUTHENTICATION" in step
        or "OTP" in code
        or "DROPPED" in reason
        or code == "BAD_REQUEST_PAYMENT_TIMED_OUT"
    ):
        return FailureCategory.USER_AUTHENTICATION_DROPOFF, True

    # 4. Insufficient Funds (Recoverable via alternative method/reminder)
    if (
        "INSUFFICIENT" in code
        or "FUNDS" in reason
        or code == "BAD_REQUEST_PAYMENT_ACCOUNT_INSUFFICIENT_BALANCE"
    ):
        return FailureCategory.INSUFFICIENT_FUNDS, True

    # 5. Fraud / Risk Block (Permanent/Non-recoverable)
    if "FRAUD" in code or "RISK" in code or "BLOCKED" in reason:
        return FailureCategory.FRAUD_RISK_BLOCK, False

    # 6. Permanent Instrument Decline (Expired card, invalid CVV, card blocked)
    if "EXPIRED" in code or "INVALID_CARD" in code or "CARD_DISABLED" in code:
        return FailureCategory.PERMANENT_INSTRUMENT_DECLINE, False

    # Default fallback
    is_transient = source in ("bank", "gateway") or "timeout" in reason
    return FailureCategory.UNKNOWN, is_transient


def parse_razorpay_webhook(
    raw_body_bytes: bytes,
    headers: Dict[str, str],
) -> ParsedRazorpayPaymentPayload:
    """
    Parses raw Razorpay webhook payload into a normalized dataclass.
    Extracts official event fields according to Razorpay API specs.
    """
    payload_json = json.loads(raw_body_bytes.decode("utf-8"))

    event_type = payload_json.get("event", "unknown")
    account_id = payload_json.get("account_id")
    event_timestamp_sec = payload_json.get("created_at")

    if event_timestamp_sec:
        created_at_dt = datetime.fromtimestamp(event_timestamp_sec, tz=timezone.utc)
    else:
        created_at_dt = datetime.now(timezone.utc)

    # Razorpay payload structure: payload -> payment -> entity
    payment_container = payload_json.get("payload", {}).get("payment", {})
    payment_entity = payment_container.get("entity", {})

    payment_id = payment_entity.get("id", "")
    order_id = payment_entity.get("order_id")
    amount_cents = payment_entity.get("amount", 0)
    currency = payment_entity.get("currency", "INR")
    status = payment_entity.get("status", "failed")
    method = payment_entity.get("method")
    description = payment_entity.get("description")

    customer_email = payment_entity.get("email")
    customer_contact = payment_entity.get("contact")
    customer_name = payment_entity.get("notes", {}).get("customer_name")

    # Error diagnostics
    error_code = payment_entity.get("error_code")
    error_description = payment_entity.get("error_description")
    error_source = payment_entity.get("error_source")
    error_step = payment_entity.get("error_step")
    error_reason = payment_entity.get("error_reason")

    # Event ID resolution: Header X-Razorpay-Event-Id if present, else fallback
    event_id = headers.get("x-razorpay-event-id") or headers.get("X-Razorpay-Event-Id")
    if not event_id:
        # Construct deterministic unique event signature from payload invariants
        event_id = f"evt_{payment_id}_{event_type}_{event_timestamp_sec}"

    failure_cat, is_transient = classify_razorpay_failure(
        error_code=error_code,
        error_source=error_source,
        error_step=error_step,
        error_reason=error_reason,
    )

    return ParsedRazorpayPaymentPayload(
        event_id=event_id,
        event_type=event_type,
        account_id=account_id,
        external_payment_id=payment_id,
        external_order_id=order_id,
        amount_cents=amount_cents,
        currency=currency,
        status=status,
        method=method,
        description=description,
        customer_email=customer_email,
        customer_contact=customer_contact,
        customer_name=customer_name,
        error_code=error_code,
        error_description=error_description,
        error_source=error_source,
        error_step=error_step,
        error_reason=error_reason,
        failure_category=failure_cat,
        is_transient_failure=is_transient,
        created_at_timestamp=created_at_dt,
        raw_payload=payload_json,
    )
