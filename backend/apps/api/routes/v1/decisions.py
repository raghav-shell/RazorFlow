"""Decisions Explorer endpoints for searching and inspecting AI and Policy verdicts."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.dependencies import get_db_session
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.recovery_attempt import RecoveryDecisionModel
from packages.persistence.models.recovery_case import RecoveryCaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decisions", tags=["Decisions Explorer"])


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


@router.get("", summary="List Global Decisions History")
async def list_decisions_endpoint(
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Returns paginated decision records across all cases for the merchant.
    Includes AI recommendation, confidence, policy verdict, and authorized action.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)

    stmt = (
        select(RecoveryDecisionModel)
        .options(selectinload(RecoveryDecisionModel.case).selectinload(RecoveryCaseModel.order))
        .where(RecoveryDecisionModel.merchant_id == merchant.id)
        .order_by(RecoveryDecisionModel.decided_at.desc())
        .offset(offset)
        .limit(limit)
    )
    decisions = (await db.execute(stmt)).scalars().all()

    items: List[Dict[str, Any]] = []
    for d in decisions:
        order_external_id = d.case.order.external_order_id if d.case and d.case.order else "unknown"
        amount_formatted = f"₹{d.case.amount_at_risk_cents / 100:.2f}" if d.case else "₹0.00"

        items.append(
            {
                "decision_id": str(d.id),
                "case_id": str(d.case_id),
                "external_order_id": order_external_id,
                "amount_formatted": amount_formatted,
                "attempt_number": d.attempt_number,
                "ai_recommended_action": d.ai_recommended_action.value,
                "ai_confidence": d.ai_confidence,
                "ai_reasoning": d.ai_reasoning,
                "policy_verdict": d.policy_verdict.value,
                "authorized_action": d.authorized_action.value,
                "policy_rule_triggered": d.policy_rule_triggered,
                "decided_at": d.decided_at.isoformat(),
            }
        )

    return {
        "merchant_slug": merchant_slug,
        "count": len(items),
        "offset": offset,
        "limit": limit,
        "items": items,
    }
