"""Pure domain enums representing financial and orchestrator states."""

from enum import Enum


class OrderStatus(str, Enum):
    """Lifecycle status of a merchant order."""

    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    """Status of an individual payment attempt at the gateway."""

    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class RecoveryCaseStatus(str, Enum):
    """
    Formal lifecycle state of a RecoveryCase aggregate root.
    Tracks the overarching unit of revenue at risk.
    """

    DETECTED = "DETECTED"
    ENRICHING = "ENRICHING"
    DIAGNOSING = "DIAGNOSING"
    STRATEGY_GENERATED = "STRATEGY_GENERATED"
    POLICY_CHECK_PENDING = "POLICY_CHECK_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    EXECUTING = "EXECUTING"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    VERIFYING = "VERIFYING"
    RECOVERED = "RECOVERED"
    UNRECOVERABLE = "UNRECOVERABLE"
    EXPIRED = "EXPIRED"
    STOPPED = "STOPPED"


class RecoveryActionType(str, Enum):
    """
    Bounded, deterministic set of executable recovery actions.
    Strategies and LLMs can only select among these actions.
    """

    PAYMENT_LINK = "PAYMENT_LINK"
    CUSTOMER_REMINDER = "CUSTOMER_REMINDER"
    WAIT_AND_REASSESS = "WAIT_AND_REASSESS"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"
    DO_NOTHING = "DO_NOTHING"


class PolicyVerdict(str, Enum):
    """Verdict rendered by the deterministic policy engine."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    MODIFIED = "MODIFIED"


class RecoveryAttemptStatus(str, Enum):
    """Execution status of a single physical recovery attempt."""

    DRAFT = "DRAFT"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class FailureCategory(str, Enum):
    """Taxonomy of classified payment root-cause failures."""

    USER_AUTHENTICATION_DROPOFF = "USER_AUTHENTICATION_DROPOFF"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    TECHNICAL_GATEWAY_TIMEOUT = "TECHNICAL_GATEWAY_TIMEOUT"
    BANK_SYSTEM_OUTAGE = "BANK_SYSTEM_OUTAGE"
    PERMANENT_INSTRUMENT_DECLINE = "PERMANENT_INSTRUMENT_DECLINE"
    FRAUD_RISK_BLOCK = "FRAUD_RISK_BLOCK"
    UNKNOWN = "UNKNOWN"
