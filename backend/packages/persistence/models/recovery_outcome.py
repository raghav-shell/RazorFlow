"""SQLAlchemy ORM model for RecoveryOutcome."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.domain.enums import RecoveryActionType
from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from packages.persistence.models.recovery_case import RecoveryCaseModel


class RecoveryOutcomeModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Final verified financial artifact reflecting recovered capital, fees, and latency.
    """

    __tablename__ = "recovery_outcomes"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_cases.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    settling_payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    successful_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    amount_recovered_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cost_incurred_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    net_recovery_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    recovery_method: Mapped[RecoveryActionType | None] = mapped_column(
        Enum(RecoveryActionType, name="recovery_action_type"),
        nullable=True,
    )
    verification_source: Mapped[str] = mapped_column(String(100), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case: Mapped[RecoveryCaseModel] = relationship("RecoveryCaseModel", back_populates="outcome")
