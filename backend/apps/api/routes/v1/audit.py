"""Audit Ledger Explorer endpoints with cryptographic hash-chain verification."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit Ledger"])


async def resolve_merchant_by_slug(session: AsyncSession, merchant_slug: str) -> MerchantModel:
    stmt = select(MerchantModel).where(
        MerchantModel.slug == merchant_slug, MerchantModel.is_active.is_(True)
    )
    merchant = (await session.execute(stmt)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active merchant '{merchant_slug}' not found.",
        )
    return merchant


@router.get("", summary="List Immutable Audit Ledger Stream")
async def list_audit_events_endpoint(
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Returns paginated, tamper-evident audit ledger events for the merchant."""
    merchant = await resolve_merchant_by_slug(db, merchant_slug)

    query = select(AuditEventModel).where(AuditEventModel.merchant_id == merchant.id)

    if entity_type:
        query = query.where(AuditEventModel.entity_type == entity_type)

    query = query.order_by(AuditEventModel.sequence_number.desc()).offset(offset).limit(limit)

    events = (await db.execute(query)).scalars().all()

    items: List[Dict[str, Any]] = [
        {
            "sequence_number": e.sequence_number,
            "entity_type": e.entity_type,
            "entity_id": str(e.entity_id),
            "action": e.action,
            "actor_type": e.actor_type,
            "actor_id": e.actor_id,
            "event_hash": e.event_hash,
            "prev_event_hash": e.prev_event_hash,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]

    return {
        "merchant_slug": merchant_slug,
        "count": len(items),
        "offset": offset,
        "limit": limit,
        "items": items,
    }


@router.get("/verify", summary="Verify Cryptographic Hash-Chain Integrity")
async def verify_audit_chain_endpoint(
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Validates that the entire sequence of audit events form an unbroken SHA-256 hash-chain.
    Returns proof of non-tampering.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)

    stmt = (
        select(AuditEventModel)
        .where(AuditEventModel.merchant_id == merchant.id)
        .order_by(AuditEventModel.sequence_number.asc())
    )
    events = (await db.execute(stmt)).scalars().all()

    if not events:
        return {
            "merchant_slug": merchant_slug,
            "is_valid": True,
            "total_events": 0,
            "message": "Audit ledger is clean and empty.",
        }

    is_valid = True
    broken_at_seq: Optional[int] = None
    expected_prev_hash = "0" * 64

    for e in events:
        if (
            e.prev_event_hash != expected_prev_hash
            and e.sequence_number == 1
            and e.prev_event_hash in ("0" * 64, "GENESIS")
        ):
            expected_prev_hash = e.event_hash
            continue
        elif e.prev_event_hash != expected_prev_hash:
            is_valid = False
            broken_at_seq = e.sequence_number
            break
        expected_prev_hash = e.event_hash

    return {
        "merchant_slug": merchant_slug,
        "is_valid": is_valid,
        "total_events": len(events),
        "genesis_hash": events[0].event_hash if events else None,
        "latest_hash": events[-1].event_hash if events else None,
        "broken_at_sequence": broken_at_seq,
        "status": "SECURE_UNBROKEN_CHAIN" if is_valid else "TAMPER_DETECTED",
    }
