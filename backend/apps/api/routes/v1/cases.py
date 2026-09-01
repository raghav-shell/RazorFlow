"""Recovery Cases query and execution endpoints with strict multi-tenant isolation."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.dependencies import get_db_session
from packages.domain.commands import RecoveryCommand
from packages.domain.enums import PaymentStatus, RecoveryActionType, RecoveryCaseStatus
from packages.orchestration.services.action_orchestrator import ActionOrchestrator
from packages.orchestration.services.verification_service import VerificationService
from packages.persistence.models.audit_event import AuditEventModel
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel, RecoveryDecisionModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel

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


async def resolve_case_by_id_or_link(
    session: AsyncSession, merchant_id: uuid.UUID, identifier: str
) -> Optional[RecoveryCaseModel]:
    """Helper to resolve recovery case by either case UUID or payment link gateway reference ID."""
    # 1. Try UUID lookup
    try:
        case_uuid = uuid.UUID(identifier)
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
                RecoveryCaseModel.id == case_uuid,
                RecoveryCaseModel.merchant_id == merchant_id,
            )
        )
        case = (await session.execute(stmt)).scalar_one_or_none()
        if case:
            return case
    except (ValueError, AttributeError):
        pass

    # 2. Try lookup by gateway_reference_id (e.g. plink_xxx) in attempts
    att_stmt = (
        select(RecoveryAttemptModel.case_id)
        .where(
            RecoveryAttemptModel.merchant_id == merchant_id,
            RecoveryAttemptModel.gateway_reference_id == identifier,
        )
        .limit(1)
    )
    matched_case_id = (await session.execute(att_stmt)).scalar_one_or_none()
    if matched_case_id:
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
                RecoveryCaseModel.id == matched_case_id,
                RecoveryCaseModel.merchant_id == merchant_id,
            )
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    return None


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


@router.get("/{case_id}", summary="Get Detailed Recovery Case by ID or Link ID")
async def get_recovery_case_endpoint(
    case_id: str,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Returns complete investigation snapshot and audit history for a single recovery case.
    Accepts either a Case UUID or a Gateway Payment Link ID.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    case = await resolve_case_by_id_or_link(db, merchant.id, case_id)

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
            AuditEventModel.entity_id == case.id,
        )
        .order_by(AuditEventModel.sequence_number.asc())
    )
    audit_events = (await db.execute(audit_stmt)).scalars().all()

    # Locate active payment link reference if present
    payment_link_id = None
    payment_link_url = None
    if case.attempts:
        for att in reversed(case.attempts):
            if att.action_type == RecoveryActionType.PAYMENT_LINK and att.gateway_reference_id:
                payment_link_id = att.gateway_reference_id
                payment_link_url = (
                    att.execution_payload.get("short_url") if att.execution_payload else None
                )
                break

    return {
        "case_id": str(case.id),
        "merchant_id": str(case.merchant_id),
        "merchant_slug": merchant_slug,
        "payment_link_id": payment_link_id,
        "payment_link_url": payment_link_url,
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


@router.get("/{case_id}/decisions", summary="Get Decisions for Recovery Case")
async def get_case_decisions_endpoint(
    case_id: str,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Returns all AI strategy decisions and policy evaluations for this case."""
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    case = await resolve_case_by_id_or_link(db, merchant.id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found.")

    stmt = (
        select(RecoveryDecisionModel)
        .where(
            RecoveryDecisionModel.case_id == case.id,
            RecoveryDecisionModel.merchant_id == merchant.id,
        )
        .order_by(RecoveryDecisionModel.attempt_number.asc())
    )
    decisions = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(d.id),
            "attempt_number": d.attempt_number,
            "eligible_candidates": d.eligible_candidate_actions,
            "ai_recommended_action": d.ai_recommended_action.value,
            "ai_confidence": d.ai_confidence,
            "ai_reasoning": d.ai_reasoning,
            "policy_verdict": d.policy_verdict.value,
            "authorized_action": d.authorized_action.value,
            "policy_rule_triggered": d.policy_rule_triggered,
            "ai_raw_response": d.ai_raw_response,
            "decided_at": d.decided_at.isoformat(),
        }
        for d in decisions
    ]


@router.get("/{case_id}/attempts", summary="Get Execution Attempts for Recovery Case")
async def get_case_attempts_endpoint(
    case_id: str,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Returns all physical execution attempts dispatched for this case."""
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    case = await resolve_case_by_id_or_link(db, merchant.id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found.")

    stmt = (
        select(RecoveryAttemptModel)
        .where(
            RecoveryAttemptModel.case_id == case.id,
            RecoveryAttemptModel.merchant_id == merchant.id,
        )
        .order_by(RecoveryAttemptModel.created_at.asc())
    )
    attempts = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": str(a.id),
            "action_type": a.action_type.value,
            "idempotency_key": a.idempotency_key,
            "status": a.status.value,
            "gateway_reference_id": a.gateway_reference_id,
            "execution_payload": a.execution_payload,
            "dispatched_at": a.dispatched_at.isoformat() if a.dispatched_at else None,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            "error_message": a.error_message,
        }
        for a in attempts
    ]


@router.get("/{case_id}/outcome", summary="Get Verified Financial Outcome")
async def get_case_outcome_endpoint(
    case_id: str,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Returns verified financial recovery outcome."""
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    case = await resolve_case_by_id_or_link(db, merchant.id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found.")

    stmt = select(RecoveryOutcomeModel).where(
        RecoveryOutcomeModel.case_id == case.id,
        RecoveryOutcomeModel.merchant_id == merchant.id,
    )
    outcome = (await db.execute(stmt)).scalar_one_or_none()

    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial outcome not yet established for case '{case_id}'.",
        )

    return {
        "id": str(outcome.id),
        "case_id": str(outcome.case_id),
        "is_successful": outcome.is_successful,
        "amount_recovered_cents": outcome.amount_recovered_cents,
        "amount_recovered_formatted": f"₹{outcome.amount_recovered_cents / 100:.2f}",
        "cost_incurred_cents": outcome.cost_incurred_cents,
        "cost_incurred_formatted": f"₹{outcome.cost_incurred_cents / 100:.2f}",
        "net_recovery_cents": outcome.net_recovery_cents,
        "net_recovery_formatted": f"₹{outcome.net_recovery_cents / 100:.2f}",
        "recovery_method": outcome.recovery_method.value if outcome.recovery_method else None,
        "verification_source": outcome.verification_source,
        "verified_at": outcome.verified_at.isoformat(),
    }


@router.post("/{case_id}/execute", summary="Execute Latest Authorized Command")
async def execute_case_command_endpoint(
    case_id: str,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Executes the latest authorized decision command via ActionOrchestrator."""
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    case = await resolve_case_by_id_or_link(db, merchant.id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found.")

    # Fetch latest decision
    dec_stmt = (
        select(RecoveryDecisionModel)
        .where(
            RecoveryDecisionModel.case_id == case.id,
            RecoveryDecisionModel.merchant_id == merchant.id,
        )
        .order_by(RecoveryDecisionModel.attempt_number.desc())
        .limit(1)
    )
    latest_decision = (await db.execute(dec_stmt)).scalar_one_or_none()

    if not latest_decision or latest_decision.authorized_action == RecoveryActionType.DO_NOTHING:
        raise HTTPException(
            status_code=400, detail="No authorized actionable command exists for this case."
        )

    attempt_number = case.current_attempt_count + 1
    command = RecoveryCommand.create(
        case_id=case.id,
        merchant_id=merchant.id,
        order_id=case.order_id,
        action_type=latest_decision.authorized_action,
        attempt_number=attempt_number,
        amount_cents=case.amount_at_risk_cents,
        currency=case.currency,
        deadline_at=case.deadline_at,
        payload=latest_decision.policy_details,
    )

    result = await ActionOrchestrator.execute_command(
        session=db,
        command=command,
        decision_id=latest_decision.id,
    )
    await db.commit()

    return {
        "case_id": str(result.case_id),
        "attempt_id": str(result.attempt_id),
        "action_type": result.action_type.value,
        "attempt_status": result.attempt_status.value,
        "case_status": result.case_status.value,
        "gateway_reference_id": result.gateway_reference_id,
        "is_duplicate": result.is_duplicate_execution,
    }


@router.post("/{case_id}/simulate-payment", summary="Simulate Customer Payment for Demo")
async def simulate_payment_endpoint(
    case_id: str,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Demo simulation endpoint: Creates a captured payment and triggers financial verification.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    case = await resolve_case_by_id_or_link(db, merchant.id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found.")

    order = await db.get(OrderModel, case.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Create captured settling payment
    payment = PaymentModel(
        merchant_id=merchant.id,
        order_id=order.id,
        external_payment_id=f"pay_sim_{uuid.uuid4().hex[:8]}",
        amount_cents=case.amount_at_risk_cents,
        currency=case.currency,
        status=PaymentStatus.CAPTURED,
        method="upi",
    )
    db.add(payment)
    await db.flush()

    verif_res = await VerificationService.verify_and_recover_case(
        session=db,
        case=case,
        settling_payment=payment,
        verification_source="DEMO_SIMULATION",
    )
    await db.commit()

    return {
        "status": "success",
        "case_id": str(case.id),
        "is_verified": verif_res.is_verified,
        "case_status": verif_res.case_status.value,
        "recovered_amount_cents": verif_res.recovered_amount_cents,
        "net_recovery_cents": verif_res.net_recovery_cents,
        "verification_source": verif_res.verification_source,
    }
