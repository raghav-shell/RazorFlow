"""Pure domain entity definitions and snapshots."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from packages.domain.enums import (
    FailureCategory,
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryAttemptStatus,
    RecoveryCaseStatus,
)
from packages.domain.value_objects import MonetaryAmount, RecoveryProbability, RiskScore


@dataclass
class CustomerSnapshot:
    id: UUID
    merchant_id: UUID
    external_customer_id: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    name: Optional[str]
    risk_score: RiskScore
    recovery_success_count: int = 0
    total_failure_count: int = 0


@dataclass
class OrderSnapshot:
    id: UUID
    merchant_id: UUID
    external_order_id: str
    amount: MonetaryAmount
    status: OrderStatus
    customer_id: Optional[UUID] = None
    receipt: Optional[str] = None


@dataclass
class PaymentSnapshot:
    id: UUID
    merchant_id: UUID
    order_id: UUID
    external_payment_id: str
    amount: MonetaryAmount
    status: PaymentStatus
    customer_id: Optional[UUID] = None
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None


@dataclass
class RecoveryCaseSnapshot:
    id: UUID
    merchant_id: UUID
    order_id: UUID
    initial_payment_id: UUID
    amount_at_risk: MonetaryAmount
    amount_recovered: MonetaryAmount
    status: RecoveryCaseStatus
    failure_category: Optional[FailureCategory]
    is_transient: bool
    current_attempt_count: int
    max_allowed_attempts: int
    deadline_at: datetime
    customer_id: Optional[UUID] = None
    diagnosis_reasoning: Optional[str] = None
    recovery_probability: Optional[RecoveryProbability] = None
    expected_recovery_value: Optional[MonetaryAmount] = None
    last_ai_confidence: Optional[float] = None
    next_action_scheduled_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def amount_at_risk_cents(self) -> int:
        return self.amount_at_risk.cents

    @property
    def amount_recovered_cents(self) -> int:
        return self.amount_recovered.cents

    @property
    def currency(self) -> str:
        return self.amount_at_risk.currency

    @property
    def metadata_json(self) -> Dict[str, Any]:
        return self.metadata


@dataclass
class CaseEnrichmentContext:
    customer: Optional[CustomerSnapshot] = None
    order: Optional[OrderSnapshot] = None
    initial_payment: Optional[PaymentSnapshot] = None
    prior_attempts: List["RecoveryAttemptSnapshot"] = field(default_factory=list)
    merchant_settings: Dict[str, Any] = field(default_factory=dict)
    has_active_payment_link: bool = False
    customer_id: Optional[UUID] = None
    historical_success_count: int = 0
    historical_failure_count: int = 0
    previous_recovery_count: int = 0
    customer_risk_tier: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if self.customer:
            if not self.customer_id:
                self.customer_id = self.customer.id
            if self.historical_success_count == 0 and self.customer.recovery_success_count > 0:
                self.historical_success_count = self.customer.recovery_success_count
            if self.historical_failure_count == 0 and self.customer.total_failure_count > 0:
                self.historical_failure_count = self.customer.total_failure_count
            if self.previous_recovery_count == 0 and self.customer.recovery_success_count > 0:
                self.previous_recovery_count = self.customer.recovery_success_count


@dataclass
class RecoveryAttemptSnapshot:
    id: UUID
    case_id: UUID
    merchant_id: UUID
    action_type: RecoveryActionType
    idempotency_key: str
    status: RecoveryAttemptStatus
    execution_payload: Dict[str, Any]
    decision_id: Optional[UUID] = None
    gateway_reference_id: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
