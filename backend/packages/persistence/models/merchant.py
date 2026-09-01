"""SQLAlchemy ORM models for Merchant (Tenant Root) and MerchantProviderConfig."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.persistence.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from packages.persistence.types import PortableJSON

if TYPE_CHECKING:
    from packages.persistence.models.customer import CustomerModel
    from packages.persistence.models.order import OrderModel
    from packages.persistence.models.recovery_case import RecoveryCaseModel


class MerchantModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tenant root entity representing an enterprise merchant.
    """

    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    provider_configs: Mapped[list[MerchantProviderConfigModel]] = relationship(
        "MerchantProviderConfigModel",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    customers: Mapped[list[CustomerModel]] = relationship(
        "CustomerModel",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[OrderModel]] = relationship(
        "OrderModel",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    recovery_cases: Mapped[list[RecoveryCaseModel]] = relationship(
        "RecoveryCaseModel",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )


class MerchantProviderConfigModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Isolates payment gateway / SMS provider credentials from Merchant identity.
    """

    __tablename__ = "merchant_provider_configs"
    __table_args__ = (UniqueConstraint("merchant_id", "provider", name="uq_merchant_provider"),)

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), default="RAZORPAY", nullable=False)
    key_id: Mapped[str] = mapped_column(String(255), nullable=False)
    key_secret_enc: Mapped[str] = mapped_column(String, nullable=False)
    webhook_secret_enc: Mapped[str] = mapped_column(String, nullable=False)
    is_test_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)

    merchant: Mapped[MerchantModel] = relationship(
        "MerchantModel",
        back_populates="provider_configs",
    )
