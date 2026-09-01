"""SQLAlchemy ORM model for Payment."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.domain.enums import PaymentStatus
from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from packages.persistence.models.order import OrderModel


class PaymentModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Payment entity tracking gateway transaction attempts and failure diagnostics.
    """

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("merchant_id", "external_payment_id", name="uq_merchant_external_payment"),
    )

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
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_payment_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        index=True,
    )
    method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Diagnostic metadata for root-cause classification
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    error_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    rzp_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[OrderModel] = relationship("OrderModel", back_populates="payments")
