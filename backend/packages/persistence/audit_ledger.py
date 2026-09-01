"""Audit Ledger Service for append-only cryptographic hash-chain recording."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.crypto import compute_audit_event_hash
from packages.persistence.models.audit_event import AuditEventModel

logger = logging.getLogger(__name__)

GENESIS_PREV_HASH = "0" * 64


class AuditLedgerService:
    """
    Manages tenant-isolated, append-only, tamper-evident cryptographic audit chains.
    """

    @classmethod
    async def record_event(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor_type: str,
        actor_id: str,
        payload: Dict[str, Any],
        state_before: Optional[Dict[str, Any]] = None,
        state_after: Optional[Dict[str, Any]] = None,
    ) -> AuditEventModel:
        """
        Appends an event to the merchant's hash chain in an atomic transaction.
        Calculates monotonically increasing sequence_number and sha256 hash chaining.
        """
        # Fetch latest audit event for this merchant with row locking to serialize sequence increments
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.merchant_id == merchant_id)
            .order_by(AuditEventModel.sequence_number.desc())
            .limit(1)
            .with_for_update()
        )
        result = await session.execute(stmt)
        last_event = result.scalar_one_or_none()

        if last_event is None:
            sequence_number = 1
            prev_event_hash = GENESIS_PREV_HASH
        else:
            sequence_number = last_event.sequence_number + 1
            prev_event_hash = last_event.event_hash

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        event_hash = compute_audit_event_hash(
            sequence_number=sequence_number,
            prev_event_hash=prev_event_hash,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload,
            timestamp_iso=now_iso,
        )

        audit_entry = AuditEventModel(
            merchant_id=merchant_id,
            sequence_number=sequence_number,
            prev_event_hash=prev_event_hash,
            event_hash=event_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            state_before=state_before,
            state_after=state_after,
            payload=payload,
            created_at=now_dt,
        )
        session.add(audit_entry)
        await session.flush()

        logger.debug(
            f"Recorded audit event #{sequence_number} for merchant {merchant_id} "
            f"[{action} on {entity_type}:{entity_id}] (hash={event_hash[:8]}...)"
        )
        return audit_entry
