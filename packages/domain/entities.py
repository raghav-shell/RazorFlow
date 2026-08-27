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
    recovery_success_count: int
    total_failure_count: int


@dataclass
class OrderSnapshot:
    id: UUID
    merchant_id: UUID
    external_order_id: str
    customer_id: Optional[UUID]
    amount: MonetaryAmount
    status: OrderStatus
    receipt: Optional[str]


@dataclass
class PaymentSnapshot:
    id: UUID
    merchant_id: UUID
    order_id: UUID
    customer_id: Optional[UUID]
    external_payment_id: str
    amount: MonetaryAmount
    status: PaymentStatus
    method: Optional[str]
    error_code: Optional[str]
    error_description: Optional[str]
    error_source: Optional[str]
    error_step: Optional[str]
    error_reason: Optional[str]


@dataclass
class RecoveryCaseSnapshot:
    id: UUID
    merchant_id: UUID
    order_id: UUID
    initial_payment_id: UUID
    customer_id: Optional[UUID]
    amount_at_risk: MonetaryAmount
    amount_recovered: MonetaryAmount
    status: RecoveryCaseStatus
    failure_category: Optional[FailureCategory]
    is_transient: bool
    diagnosis_reasoning: Optional[str]
    recovery_probability: Optional[RecoveryProbability]
    expected_recovery_value: Optional[MonetaryAmount]
    last_ai_confidence: Optional[float]
    current_attempt_count: int
    max_allowed_attempts: int
    deadline_at: datetime
    next_action_scheduled_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseEnrichmentContext:
    customer: Optional[CustomerSnapshot]
    order: OrderSnapshot
    initial_payment: PaymentSnapshot
    prior_attempts: List["RecoveryAttemptSnapshot"] = field(default_factory=list)
    merchant_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAttemptSnapshot:
    id: UUID
    case_id: UUID
    merchant_id: UUID
    decision_id: Optional[UUID]
    action_type: RecoveryActionType
    idempotency_key: str
    status: RecoveryAttemptStatus
    execution_payload: Dict[str, Any]
    gateway_reference_id: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
