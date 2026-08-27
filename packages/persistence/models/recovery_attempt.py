"""SQLAlchemy ORM models for RecoveryDecision and RecoveryAttempt."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.domain.enums import PolicyVerdict, RecoveryActionType, RecoveryAttemptStatus
from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from packages.persistence.types import PortableArray, PortableJSON

if TYPE_CHECKING:
    from packages.persistence.models.recovery_case import RecoveryCaseModel


class RecoveryDecisionModel(Base, UUIDPrimaryKeyMixin):
    """
    Immutable audit of AI strategy proposal and deterministic Policy Engine verdict.
    """

    __tablename__ = "recovery_decisions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Bounded candidate set
    eligible_candidate_actions: Mapped[list[str]] = mapped_column(
        PortableArray,
        default=list,
        nullable=False,
    )

    # AI Proposal
    ai_recommended_action: Mapped[RecoveryActionType] = mapped_column(
        Enum(RecoveryActionType, name="recovery_action_type"),
        nullable=False,
    )
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    ai_raw_response: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)

    # Policy Verdict
    policy_verdict: Mapped[PolicyVerdict] = mapped_column(
        Enum(PolicyVerdict, name="policy_verdict_type"),
        nullable=False,
    )
    authorized_action: Mapped[RecoveryActionType] = mapped_column(
        Enum(RecoveryActionType, name="recovery_action_type"),
        nullable=False,
    )
    policy_rule_triggered: Mapped[str | None] = mapped_column(String(255), nullable=True)
    policy_details: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)

    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case: Mapped[RecoveryCaseModel] = relationship("RecoveryCaseModel", back_populates="decisions")
    attempts: Mapped[list[RecoveryAttemptModel]] = relationship(
        "RecoveryAttemptModel",
        back_populates="decision",
    )


class RecoveryAttemptModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Physical execution attempt with unique idempotency key and gateway tracking IDs.
    """

    __tablename__ = "recovery_attempts"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_decisions.id", ondelete="SET NULL"),
        nullable=True,
    )

    action_type: Mapped[RecoveryActionType] = mapped_column(
        Enum(RecoveryActionType, name="recovery_action_type"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    status: Mapped[RecoveryAttemptStatus] = mapped_column(
        Enum(RecoveryAttemptStatus, name="recovery_attempt_status"),
        default=RecoveryAttemptStatus.DRAFT,
        nullable=False,
        index=True,
    )

    execution_payload: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)
    gateway_reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    gateway_response: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped[RecoveryCaseModel] = relationship("RecoveryCaseModel", back_populates="attempts")
    decision: Mapped[RecoveryDecisionModel | None] = relationship(
        "RecoveryDecisionModel", back_populates="attempts"
    )
