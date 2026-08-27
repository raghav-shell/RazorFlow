"""SQLAlchemy ORM model for AuditEvent (Append-only Cryptographic Hash-Chain Ledger)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from packages.persistence.base import Base, UUIDPrimaryKeyMixin
from packages.persistence.types import PortableJSON


class AuditEventModel(Base, UUIDPrimaryKeyMixin):
    """
    Append-only tamper-evident audit ledger record.
    Chained cryptographically per tenant via SHA-256 hashes.
    """

    __tablename__ = "audit_events"
    __table_args__ = (
        UniqueConstraint("merchant_id", "sequence_number", name="uq_merchant_audit_seq"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prev_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)

    state_before: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    state_after: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    payload: Mapped[dict] = mapped_column(PortableJSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
