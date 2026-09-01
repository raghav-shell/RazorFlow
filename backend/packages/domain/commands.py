"""Immutable authorized domain commands."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from packages.domain.enums import RecoveryActionType


@dataclass(frozen=True)
class RecoveryCommand:
    """
    Immutable, provider-agnostic recovery command authorized by the Policy Engine.
    Consumed downstream by Phase 4 Action Executors.
    """

    command_id: uuid.UUID
    case_id: uuid.UUID
    merchant_id: uuid.UUID
    order_id: uuid.UUID
    action_type: RecoveryActionType
    idempotency_key: str
    amount_at_risk_cents: int
    currency: str
    deadline_at: datetime
    payload: Dict[str, Any] = field(default_factory=dict)
    authorized_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        case_id: uuid.UUID,
        merchant_id: uuid.UUID,
        order_id: uuid.UUID,
        action_type: RecoveryActionType,
        attempt_number: int,
        amount_cents: int,
        currency: str,
        deadline_at: datetime,
        payload: Dict[str, Any] | None = None,
    ) -> "RecoveryCommand":
        """Factory creating a unique deterministic command with idempotency key."""
        idempotency_key = f"cmd_{case_id}_{attempt_number}_{action_type.value}"
        return cls(
            command_id=uuid.uuid4(),
            case_id=case_id,
            merchant_id=merchant_id,
            order_id=order_id,
            action_type=action_type,
            idempotency_key=idempotency_key,
            amount_at_risk_cents=amount_cents,
            currency=currency,
            deadline_at=deadline_at,
            payload=payload or {},
        )
