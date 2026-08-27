"""SQLAlchemy ORM model for Customer."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from packages.persistence.models.merchant import MerchantModel
    from packages.persistence.models.order import OrderModel


class CustomerModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Customer entity holding risk scores, contact identifiers, and historical recovery counters.
    """

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("merchant_id", "external_customer_id", name="uq_merchant_customer"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recovery_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    merchant: Mapped[MerchantModel] = relationship(
        "MerchantModel",
        back_populates="customers",
    )
    orders: Mapped[list[OrderModel]] = relationship(
        "OrderModel",
        back_populates="customer",
    )
