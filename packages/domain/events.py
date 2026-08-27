"""Pure domain events representing asynchronous lifecycle occurrences."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from packages.domain.enums import (
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.value_objects import MonetaryAmount


@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    merchant_id: Optional[UUID] = None


@dataclass(frozen=True)
class PaymentFailedRevenueEvent(DomainEvent):
    order_id: UUID = field(default_factory=uuid4)
    payment_id: UUID = field(default_factory=uuid4)
    external_order_id: str = ""
    external_payment_id: str = ""
    amount: MonetaryAmount = field(default_factory=lambda: MonetaryAmount(cents=0))
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_reason: Optional[str] = None


@dataclass(frozen=True)
class CaseStateChangedEvent(DomainEvent):
    case_id: UUID = field(default_factory=uuid4)
    old_status: RecoveryCaseStatus = RecoveryCaseStatus.DETECTED
    new_status: RecoveryCaseStatus = RecoveryCaseStatus.DETECTED
    reason: str = ""


@dataclass(frozen=True)
class RecoveryAttemptDispatchedEvent(DomainEvent):
    attempt_id: UUID = field(default_factory=uuid4)
    case_id: UUID = field(default_factory=uuid4)
    action_type: RecoveryActionType = RecoveryActionType.PAYMENT_LINK
    idempotency_key: str = ""


@dataclass(frozen=True)
class RecoveryOutcomeVerifiedEvent(DomainEvent):
    case_id: UUID = field(default_factory=uuid4)
    is_successful: bool = False
    amount_recovered: MonetaryAmount = field(default_factory=lambda: MonetaryAmount(cents=0))
    settling_payment_id: Optional[UUID] = None
    verification_source: str = "RAZORPAY_WEBHOOK"
