"""SQLAlchemy ORM model for RecoveryCase (Aggregate Root)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.domain.enums import RecoveryCaseStatus
from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from packages.persistence.types import PortableJSON

if TYPE_CHECKING:
    from packages.persistence.models.customer import CustomerModel
    from packages.persistence.models.merchant import MerchantModel
    from packages.persistence.models.order import OrderModel
    from packages.persistence.models.recovery_attempt import (
        RecoveryAttemptModel,
        RecoveryDecisionModel,
    )
    from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel


class RecoveryCaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Aggregate root representing a recoverable unit of revenue.
    """

    __tablename__ = "recovery_cases"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initial_payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount_at_risk_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_recovered_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    status: Mapped[RecoveryCaseStatus] = mapped_column(
        Enum(RecoveryCaseStatus, name="recovery_case_status"),
        default=RecoveryCaseStatus.DETECTED,
        nullable=False,
        index=True,
    )

    # Root Cause Diagnostics
    failure_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_transient: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    diagnosis_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ML & AI Estimations
    recovery_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_recovery_value_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Lifecycle & Quota Controls
    current_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_allowed_attempts: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_action_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_json: Mapped[dict] = mapped_column(
        "metadata", PortableJSON, default=dict, nullable=False
    )

    # Relationships
    merchant: Mapped[MerchantModel] = relationship("MerchantModel", back_populates="recovery_cases")
    order: Mapped[OrderModel] = relationship("OrderModel", back_populates="recovery_cases")
    customer: Mapped[CustomerModel | None] = relationship("CustomerModel")
    attempts: Mapped[list[RecoveryAttemptModel]] = relationship(
        "RecoveryAttemptModel",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list[RecoveryDecisionModel]] = relationship(
        "RecoveryDecisionModel",
        back_populates="case",
        cascade="all, delete-orphan",
    )
    outcome: Mapped[RecoveryOutcomeModel | None] = relationship(
        "RecoveryOutcomeModel",
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan",
    )


# Partial unique index ensuring ONLY ONE active recovery case per order
Index(
    "uq_active_order_recovery_case",
    RecoveryCaseModel.merchant_id,
    RecoveryCaseModel.order_id,
    unique=True,
    postgresql_where=(
        RecoveryCaseModel.status.not_in(
            [
                RecoveryCaseStatus.RECOVERED,
                RecoveryCaseStatus.UNRECOVERABLE,
                RecoveryCaseStatus.EXPIRED,
                RecoveryCaseStatus.STOPPED,
            ]
        )
    ),
)
