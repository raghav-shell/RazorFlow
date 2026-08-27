"""SQLAlchemy ORM model for Order."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.domain.enums import OrderStatus
from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from packages.persistence.models.customer import CustomerModel
    from packages.persistence.models.merchant import MerchantModel
    from packages.persistence.models.payment import PaymentModel
    from packages.persistence.models.recovery_case import RecoveryCaseModel


class OrderModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Order entity tracking commercial transaction value and lifecycle state.
    """

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("merchant_id", "external_order_id", name="uq_merchant_external_order"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_order_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.CREATED,
        nullable=False,
        index=True,
    )
    receipt: Mapped[str | None] = mapped_column(String(255), nullable=True)

    merchant: Mapped[MerchantModel] = relationship("MerchantModel", back_populates="orders")
    customer: Mapped[CustomerModel | None] = relationship("CustomerModel", back_populates="orders")
    payments: Mapped[list[PaymentModel]] = relationship(
        "PaymentModel",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    recovery_cases: Mapped[list[RecoveryCaseModel]] = relationship(
        "RecoveryCaseModel",
        back_populates="order",
    )
