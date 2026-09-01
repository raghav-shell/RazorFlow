"""Policy Studio endpoints for configuring guardrails, versioning, and impact preview."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.dependencies import get_db_session
from packages.domain.entities import CaseEnrichmentContext, CustomerSnapshot, RecoveryCaseSnapshot
from packages.domain.enums import FailureCategory, RecoveryActionType, RecoveryCaseStatus
from packages.domain.policy.engine import PolicyEngine
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.value_objects import MonetaryAmount, RiskScore
from packages.persistence.audit_ledger import AuditLedgerService
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["Policy Studio"])


class PolicyUpdateRequest(BaseModel):
    max_allowed_attempts: int = Field(2, ge=1, le=5)
    recovery_window_hours: int = Field(72, ge=1, le=168)
    cooldown_period_minutes: int = Field(30, ge=0, le=1440)
    high_value_escalation_threshold_cents: int = Field(5000000, ge=100000)
    disallowed_actions: List[RecoveryActionType] = Field(default_factory=list)
    require_human_escalation_for_high_risk: bool = Field(True)
    auto_retry_transient_failures: bool = Field(True)


class PolicyPreviewRequest(BaseModel):
    candidate_action: RecoveryActionType
    amount_at_risk_cents: int
    current_attempt_count: int = 0
    failure_category: FailureCategory = FailureCategory.USER_AUTHENTICATION_DROPOFF
    is_transient: bool = False
    customer_risk_score: float = 0.1
    policy_override: Optional[PolicyUpdateRequest] = None


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


async def get_or_create_policy_config(
    session: AsyncSession, merchant: MerchantModel
) -> tuple[MerchantProviderConfigModel, MerchantPolicySnapshot]:
    settings = get_settings()
    prov_stmt = select(MerchantProviderConfigModel).where(
        MerchantProviderConfigModel.merchant_id == merchant.id,
        MerchantProviderConfigModel.provider == "RAZORPAY",
        MerchantProviderConfigModel.is_active.is_(True),
    )
    prov_cfg = (await session.execute(prov_stmt)).scalar_one_or_none()

    if not prov_cfg:
        prov_cfg = MerchantProviderConfigModel(
            merchant_id=merchant.id,
            provider="RAZORPAY",
            key_id=settings.RAZORPAY_KEY_ID or "rzp_test_placeholder",
            key_secret_enc=settings.RAZORPAY_KEY_SECRET or "rzp_test_secret",
            webhook_secret_enc=settings.RAZORPAY_WEBHOOK_SECRET or "rzp_webhook_secret",
            is_test_mode=settings.RAZORPAY_MODE == "test",
            is_active=True,
            config_json={"policy_version": 1, "policy_history": []},
        )
        session.add(prov_cfg)
        await session.flush()
    else:
        # Synchronize provider credentials from settings if configured
        if settings.RAZORPAY_KEY_ID:
            prov_cfg.key_id = settings.RAZORPAY_KEY_ID
        if settings.RAZORPAY_KEY_SECRET:
            prov_cfg.key_secret_enc = settings.RAZORPAY_KEY_SECRET
        if settings.RAZORPAY_WEBHOOK_SECRET:
            prov_cfg.webhook_secret_enc = settings.RAZORPAY_WEBHOOK_SECRET
        await session.flush()

    raw_policy = prov_cfg.config_json.get("policy", {})
    policy_version = prov_cfg.config_json.get("policy_version", 1)

    disallowed_enums = [
        RecoveryActionType(a)
        for a in raw_policy.get("disallowed_actions", [])
        if a in RecoveryActionType._value2member_map_
    ]

    snapshot = MerchantPolicySnapshot(
        policy_version=policy_version,
        max_allowed_attempts=raw_policy.get("max_allowed_attempts", 2),
        recovery_window_hours=raw_policy.get("recovery_window_hours", 72),
        cooldown_period_minutes=raw_policy.get("cooldown_period_minutes", 30),
        high_value_escalation_threshold_cents=raw_policy.get(
            "high_value_escalation_threshold_cents", 5000000
        ),
        disallowed_actions=disallowed_enums,
        require_human_escalation_for_high_risk=raw_policy.get(
            "require_human_escalation_for_high_risk", True
        ),
        auto_retry_transient_failures=raw_policy.get("auto_retry_transient_failures", True),
    )
    return prov_cfg, snapshot


@router.get("", summary="Get Active Policy Configuration and History")
async def get_policy_config_endpoint(
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Returns active merchant policy rules and immutable policy version history."""
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    prov_cfg, snapshot = await get_or_create_policy_config(db, merchant)

    policy_history = prov_cfg.config_json.get("policy_history", [])

    return {
        "merchant_slug": merchant_slug,
        "active_policy": {
            "policy_version": snapshot.policy_version,
            "max_allowed_attempts": snapshot.max_allowed_attempts,
            "recovery_window_hours": snapshot.recovery_window_hours,
            "cooldown_period_minutes": snapshot.cooldown_period_minutes,
            "high_value_escalation_threshold_cents": snapshot.high_value_escalation_threshold_cents,
            "high_value_escalation_threshold_formatted": f"₹{snapshot.high_value_escalation_threshold_cents / 100:.2f}",
            "disallowed_actions": [a.value for a in snapshot.disallowed_actions],
            "require_human_escalation_for_high_risk": snapshot.require_human_escalation_for_high_risk,
            "auto_retry_transient_failures": snapshot.auto_retry_transient_failures,
        },
        "history": policy_history,
    }


@router.post("", summary="Update Policy Rules (Creates New Immutable Version)")
async def update_policy_endpoint(
    request: PolicyUpdateRequest,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Updates policy rules and bumps policy_version.
    Preserves all historical decisions and creates an auditable policy change event.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    prov_cfg, current_snapshot = await get_or_create_policy_config(db, merchant)

    new_version = current_snapshot.policy_version + 1
    new_policy_dict = {
        "max_allowed_attempts": request.max_allowed_attempts,
        "recovery_window_hours": request.recovery_window_hours,
        "cooldown_period_minutes": request.cooldown_period_minutes,
        "high_value_escalation_threshold_cents": request.high_value_escalation_threshold_cents,
        "disallowed_actions": [a.value for a in request.disallowed_actions],
        "require_human_escalation_for_high_risk": request.require_human_escalation_for_high_risk,
        "auto_retry_transient_failures": request.auto_retry_transient_failures,
    }

    history = list(prov_cfg.config_json.get("policy_history", []))
    history.append(
        {
            "version": current_snapshot.policy_version,
            "archived_policy": {
                "max_allowed_attempts": current_snapshot.max_allowed_attempts,
                "recovery_window_hours": current_snapshot.recovery_window_hours,
                "cooldown_period_minutes": current_snapshot.cooldown_period_minutes,
                "high_value_escalation_threshold_cents": current_snapshot.high_value_escalation_threshold_cents,
                "disallowed_actions": [a.value for a in current_snapshot.disallowed_actions],
            },
        }
    )

    prov_cfg.config_json = {
        **prov_cfg.config_json,
        "policy": new_policy_dict,
        "policy_version": new_version,
        "policy_history": history,
    }
    await db.flush()

    await AuditLedgerService.record_event(
        session=db,
        merchant_id=merchant.id,
        entity_type="POLICY_CONFIG",
        entity_id=prov_cfg.id,
        action="POLICY_VERSION_CREATED",
        actor_type="MERCHANT_ADMIN",
        actor_id=merchant_slug,
        payload={"policy_version": new_version, "rules": new_policy_dict},
    )
    await db.commit()

    return {
        "status": "success",
        "policy_version": new_version,
        "message": f"Policy updated to version {new_version}. Historical decision records preserved.",
        "active_policy": {
            **new_policy_dict,
            "policy_version": new_version,
            "high_value_escalation_threshold_formatted": f"₹{request.high_value_escalation_threshold_cents / 100:.2f}",
        },
    }


@router.post("/preview", summary="Policy Impact Preview Simulator")
async def preview_policy_impact_endpoint(
    request: PolicyPreviewRequest,
    merchant_slug: str = Query(..., description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Simulates how a policy configuration evaluates a specific candidate action.
    Helps merchants preview the effect of changing thresholds before applying.
    """
    merchant = await resolve_merchant_by_slug(db, merchant_slug)
    _, active_snapshot = await get_or_create_policy_config(db, merchant)

    if request.policy_override:
        policy = MerchantPolicySnapshot(
            policy_version=999,
            max_allowed_attempts=request.policy_override.max_allowed_attempts,
            recovery_window_hours=request.policy_override.recovery_window_hours,
            cooldown_period_minutes=request.policy_override.cooldown_period_minutes,
            high_value_escalation_threshold_cents=request.policy_override.high_value_escalation_threshold_cents,
            disallowed_actions=request.policy_override.disallowed_actions,
            require_human_escalation_for_high_risk=request.policy_override.require_human_escalation_for_high_risk,
            auto_retry_transient_failures=request.policy_override.auto_retry_transient_failures,
        )
    else:
        policy = active_snapshot

    case_snapshot = RecoveryCaseSnapshot(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        order_id=uuid.uuid4(),
        initial_payment_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        amount_at_risk=MonetaryAmount.from_paise(request.amount_at_risk_cents, merchant.currency),
        amount_recovered=MonetaryAmount.from_paise(0, merchant.currency),
        status=RecoveryCaseStatus.DIAGNOSING,
        failure_category=request.failure_category,
        is_transient=request.is_transient,
        current_attempt_count=request.current_attempt_count,
        max_allowed_attempts=policy.max_allowed_attempts,
        deadline_at=datetime.now(timezone.utc) + timedelta(hours=72),
        created_at=datetime.now(timezone.utc),
    )

    cust_snap = CustomerSnapshot(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        external_customer_id="cust_prev",
        email="prev@example.com",
        phone=None,
        name="Preview User",
        risk_score=RiskScore(score=request.customer_risk_score),
        recovery_success_count=4,
        total_failure_count=1,
    )

    context = CaseEnrichmentContext(customer=cust_snap)

    evaluation = PolicyEngine.evaluate(
        proposed_action=request.candidate_action,
        case=case_snapshot,
        context=context,
        policy=policy,
    )

    return {
        "candidate_action": request.candidate_action.value,
        "amount_at_risk_formatted": f"₹{request.amount_at_risk_cents / 100:.2f}",
        "policy_verdict": evaluation.verdict.value,
        "authorized_action": evaluation.authorized_action.value,
        "policy_rule_triggered": evaluation.rule_code,
        "reasoning": evaluation.reason,
        "was_overridden": evaluation.authorized_action != request.candidate_action,
    }
