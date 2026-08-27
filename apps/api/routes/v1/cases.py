"""Recovery Cases query endpoints with strict multi-tenant isolation."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.dependencies import get_db_session
from packages.domain.enums import RecoveryCaseStatus
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.recovery_case import RecoveryCaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["Recovery Cases"])


async def resolve_merchant_by_slug(session: AsyncSession, merchant_slug: str) -> MerchantModel:
    """Helper to resolve merchant by slug or raise HTTP 404."""
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


@router.get("", summary="List Recovery Cases for Merchant")
async def list_recovery_cases_endpoint(
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    case_status: Optional[RecoveryCaseStatus] = Query(
        None, alias="status", description="Filter by case status"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Returns paginated recovery cases belonging exclusively to the requested merchant tenant.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)

    query = (
        select(RecoveryCaseModel)
        .options(
            selectinload(RecoveryCaseModel.order),
            selectinload(RecoveryCaseModel.customer),
        )
        .where(RecoveryCaseModel.merchant_id == merchant.id)
    )

    if case_status is not None:
        query = query.where(RecoveryCaseModel.status == case_status)

    query = query.order_by(RecoveryCaseModel.created_at.desc()).offset(offset).limit(limit)

    results = (await db.execute(query)).scalars().all()

    items: List[Dict[str, Any]] = []
    for c in results:
        items.append(
            {
                "case_id": str(c.id),
                "order_id": str(c.order_id),
                "external_order_id": c.order.external_order_id if c.order else "unknown",
                "customer_id": str(c.customer_id) if c.customer_id else None,
                "customer_name": c.customer.name if c.customer else "Unknown",
                "amount_at_risk_cents": c.amount_at_risk_cents,
                "amount_at_risk_formatted": f"₹{c.amount_at_risk_cents / 100:.2f}",
                "amount_recovered_cents": c.amount_recovered_cents,
                "currency": c.currency,
                "status": c.status.value,
                "failure_category": c.failure_category,
                "is_transient": c.is_transient,
                "current_attempt_count": c.current_attempt_count,
                "max_allowed_attempts": c.max_allowed_attempts,
                "deadline_at": c.deadline_at.isoformat() if c.deadline_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
        )

    return {
        "merchant_slug": merchant_slug,
        "count": len(items),
        "offset": offset,
        "limit": limit,
        "items": items,
    }


@router.get("/{case_id}", summary="Get Detailed Recovery Case by ID")
async def get_recovery_case_endpoint(
    case_id: uuid.UUID,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Returns complete investigation snapshot and audit history for a single recovery case.
    Strictly verifies merchant boundary to prevent cross-tenant access.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)

    stmt = (
        select(RecoveryCaseModel)
        .options(
            selectinload(RecoveryCaseModel.order),
            selectinload(RecoveryCaseModel.customer),
            selectinload(RecoveryCaseModel.attempts),
            selectinload(RecoveryCaseModel.decisions),
            selectinload(RecoveryCaseModel.outcome),
        )
        .where(
            RecoveryCaseModel.id == case_id,
            RecoveryCaseModel.merchant_id == merchant.id,
        )
    )
    case = (await db.execute(stmt)).scalar_one_or_none()

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case '{case_id}' not found for merchant '{merchant_slug}'.",
        )

    # Fetch audit events for this case
    audit_stmt = (
        select(AuditEventModel)
        .where(
            AuditEventModel.merchant_id == merchant.id,
            AuditEventModel.entity_id == case_id,
        )
        .order_by(AuditEventModel.sequence_number.asc())
    )
    audit_events = (await db.execute(audit_stmt)).scalars().all()

    return {
        "case_id": str(case.id),
        "merchant_id": str(case.merchant_id),
        "merchant_slug": merchant_slug,
        "order": {
            "id": str(case.order_id),
            "external_order_id": case.order.external_order_id if case.order else "unknown",
            "amount_cents": case.order.amount_cents if case.order else case.amount_at_risk_cents,
            "status": case.order.status.value if case.order else "unknown",
        },
        "customer": {
            "id": str(case.customer.id) if case.customer else None,
            "name": case.customer.name if case.customer else "Unknown",
            "email": case.customer.email if case.customer else None,
            "phone": case.customer.phone if case.customer else None,
            "risk_score": case.customer.risk_score if case.customer else 0.0,
        }
        if case.customer
        else None,
        "amount_at_risk_cents": case.amount_at_risk_cents,
        "amount_at_risk_formatted": f"₹{case.amount_at_risk_cents / 100:.2f}",
        "amount_recovered_cents": case.amount_recovered_cents,
        "currency": case.currency,
        "status": case.status.value,
        "failure_category": case.failure_category,
        "is_transient": case.is_transient,
        "diagnosis_reasoning": case.diagnosis_reasoning,
        "current_attempt_count": case.current_attempt_count,
        "max_allowed_attempts": case.max_allowed_attempts,
        "deadline_at": case.deadline_at.isoformat() if case.deadline_at else None,
        "enrichment_context": case.metadata_json.get("enrichment_context", {}),
        "metadata": case.metadata_json,
        "audit_trail": [
            {
                "sequence_number": a.sequence_number,
                "action": a.action,
                "actor_type": a.actor_type,
                "actor_id": a.actor_id,
                "event_hash": a.event_hash,
                "prev_event_hash": a.prev_event_hash,
                "payload": a.payload,
                "created_at": a.created_at.isoformat(),
            }
            for a in audit_events
        ],
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }
