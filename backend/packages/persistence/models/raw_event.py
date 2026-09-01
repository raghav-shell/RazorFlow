"""SQLAlchemy ORM model for RawWebhookEvent."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.base import Base, UUIDPrimaryKeyMixin
from packages.persistence.types import PortableJSON


class RawWebhookEventModel(Base, UUIDPrimaryKeyMixin):
    """
    Immutable raw webhook staging record received from payment gateways.
    Guarantees immediate zero-loss persistence and idempotency.
    """

    __tablename__ = "raw_webhook_events"
    __table_args__ = (UniqueConstraint("merchant_id", "event_id", name="uq_merchant_event"),)

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), default="RAZORPAY", nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(PortableJSON, nullable=False)
    signature: Mapped[str] = mapped_column(String(255), nullable=False)
    headers: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
