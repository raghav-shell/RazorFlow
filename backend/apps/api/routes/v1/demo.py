"""Demo Scenarios Launcher orchestrating controlled evaluator workflows."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.dependencies import get_db_session
from packages.adapters.ai.mock_adapter import MockStrategyAIAdapter
from packages.adapters.razorpay.mock_gateway_adapter import MockPaymentGatewayAdapter
from packages.domain.commands import RecoveryCommand
from packages.domain.entities import CaseEnrichmentContext, CustomerSnapshot
from packages.domain.enums import (
    FailureCategory,
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryCaseStatus,
)
from packages.domain.policy.snapshot import MerchantPolicySnapshot
from packages.domain.value_objects import RiskScore
from packages.orchestration.services.action_orchestrator import ActionOrchestrator
from packages.orchestration.services.ai_decision_service import AIDecisionService
from packages.orchestration.services.verification_service import VerificationService
from packages.persistence.models.customer import CustomerModel
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import (
    RecoveryAttemptModel,
    RecoveryDecisionModel,
)
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo Controller"])


class DemoScenarioRequest(BaseModel):
    scenario_id: str  # "scenario_1", "scenario_2", "scenario_3", "scenario_4"


async def get_or_create_demo_merchant(session: AsyncSession, merchant_slug: str) -> MerchantModel:
    settings = get_settings()
    stmt = select(MerchantModel).where(MerchantModel.slug == merchant_slug)
    merchant = (await session.execute(stmt)).scalar_one_or_none()
    if not merchant:
        merchant = MerchantModel(
            name="Demo Merchant Enterprise",
            slug=merchant_slug,
            currency="INR",
            is_active=True,
        )
        session.add(merchant)
        await session.flush()

        prov_cfg = MerchantProviderConfigModel(
            merchant_id=merchant.id,
            provider="RAZORPAY",
            key_id=settings.RAZORPAY_KEY_ID or "rzp_test_demo_key",
            key_secret_enc=settings.RAZORPAY_KEY_SECRET or "rzp_test_demo_secret",
            webhook_secret_enc=settings.RAZORPAY_WEBHOOK_SECRET or "rzp_whsec_demo",
            is_test_mode=settings.RAZORPAY_MODE == "test",
            is_active=True,
            config_json={"policy_version": 1},
        )
        session.add(prov_cfg)
        await session.flush()
    else:
        # Synchronize provider credentials from settings if configured
        prov_stmt = select(MerchantProviderConfigModel).where(
            MerchantProviderConfigModel.merchant_id == merchant.id,
            MerchantProviderConfigModel.provider == "RAZORPAY",
            MerchantProviderConfigModel.is_active.is_(True),
        )
        existing_prov_cfg = (await session.execute(prov_stmt)).scalar_one_or_none()
        if existing_prov_cfg:
            if settings.RAZORPAY_KEY_ID:
                existing_prov_cfg.key_id = settings.RAZORPAY_KEY_ID
            if settings.RAZORPAY_KEY_SECRET:
                existing_prov_cfg.key_secret_enc = settings.RAZORPAY_KEY_SECRET
            if settings.RAZORPAY_WEBHOOK_SECRET:
                existing_prov_cfg.webhook_secret_enc = settings.RAZORPAY_WEBHOOK_SECRET
            await session.flush()

    return merchant


@router.post("/seed", summary="Launch Controlled Evaluator Scenario")
async def seed_demo_scenario_endpoint(
    request: DemoScenarioRequest,
    merchant_slug: str = Query("demo-store", description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Executes real backend pipelines for one of the 4 official demo scenarios:
    - scenario_1: Successful Payment Link Recovery
    - scenario_2: Bank Outage Cooldown (Wait & Reassess)
    - scenario_3: High Value Escalation (Policy Override)
    - scenario_4: AI Timeout Fallback to Deterministic ERV
    """
    merchant = await get_or_create_demo_merchant(db, merchant_slug)
    now = datetime.now(timezone.utc)
    mock_gateway = MockPaymentGatewayAdapter()

    if request.scenario_id == "scenario_1":
        # SCENARIO 1: Full successful recovery
        customer = CustomerModel(
            merchant_id=merchant.id,
            external_customer_id=f"cust_{uuid.uuid4().hex[:6]}",
            name="Aarav Sharma",
            email="aarav.sharma@example.com",
            phone="+919876543210",
            risk_score=0.08,
            recovery_success_count=7,
            total_failure_count=1,
        )
        db.add(customer)
        await db.flush()

        order = OrderModel(
            merchant_id=merchant.id,
            customer_id=customer.id,
            external_order_id=f"ord_sc1_{uuid.uuid4().hex[:6]}",
            amount_cents=450000,  # ₹4,500.00
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        db.add(order)
        await db.flush()

        init_payment = PaymentModel(
            merchant_id=merchant.id,
            order_id=order.id,
            customer_id=customer.id,
            external_payment_id=f"pay_init_{uuid.uuid4().hex[:6]}",
            amount_cents=450000,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code="BAD_REQUEST_ERROR",
            error_description="Customer dropped off at UPI MPIN screen",
        )
        db.add(init_payment)
        await db.flush()

        case = RecoveryCaseModel(
            merchant_id=merchant.id,
            order_id=order.id,
            customer_id=customer.id,
            initial_payment_id=init_payment.id,
            amount_at_risk_cents=450000,
            amount_recovered_cents=0,
            currency="INR",
            status=RecoveryCaseStatus.DIAGNOSING,
            failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
            is_transient=False,
            diagnosis_reasoning="UPI authentication dropoff during checkout. High repeat customer with 87% lifetime success rate.",
            current_attempt_count=0,
            max_allowed_attempts=2,
            deadline_at=now + timedelta(hours=72),
        )
        db.add(case)
        await db.flush()

        ai_adapter = MockStrategyAIAdapter(
            force_action=RecoveryActionType.PAYMENT_LINK,
            force_confidence=0.94,
            force_diagnosis="VIP customer dropped off during authentication.",
            force_rationale="Issuing a hosted payment link offers highest recovery probability (0.78).",
        )
        cust_snap = CustomerSnapshot(
            id=customer.id,
            merchant_id=merchant.id,
            external_customer_id=customer.external_customer_id,
            email=customer.email,
            phone=customer.phone,
            name=customer.name,
            risk_score=RiskScore(score=customer.risk_score),
            recovery_success_count=customer.recovery_success_count,
            total_failure_count=customer.total_failure_count,
        )
        enrichment_ctx = CaseEnrichmentContext(customer=cust_snap)

        dec_result = await AIDecisionService.evaluate_with_ai(
            session=db,
            case=case,
            context=enrichment_ctx,
            policy=MerchantPolicySnapshot(),
            ai_client=ai_adapter,
        )

        cmd = dec_result.authorized_command
        if not cmd:
            cmd = RecoveryCommand.create(
                case_id=case.id,
                merchant_id=merchant.id,
                order_id=order.id,
                action_type=dec_result.policy_evaluation.authorized_action,
                attempt_number=1,
                amount_cents=case.amount_at_risk_cents,
                currency=case.currency,
                deadline_at=case.deadline_at,
            )

        exec_result = await ActionOrchestrator.execute_command(
            session=db,
            command=cmd,
            decision_id=dec_result.decision_record_id,
            gateway=mock_gateway,
        )

        # Simulate Customer Payment & Verification
        settling_pay = PaymentModel(
            merchant_id=merchant.id,
            order_id=order.id,
            customer_id=customer.id,
            external_payment_id=f"pay_settled_{uuid.uuid4().hex[:6]}",
            amount_cents=450000,
            currency="INR",
            status=PaymentStatus.CAPTURED,
            method="upi",
        )
        db.add(settling_pay)
        await db.flush()

        verif_res = await VerificationService.verify_and_recover_case(
            session=db,
            case=case,
            settling_payment=settling_pay,
            verification_source="DEMO_SCENARIO_1",
            gateway_reference_id=exec_result.gateway_reference_id,
        )
        await db.commit()

        return {
            "scenario": "scenario_1",
            "title": "Scenario 1: Successful Payment Link Recovery",
            "case_id": str(case.id),
            "order_id": order.external_order_id,
            "amount_formatted": "₹4,500.00",
            "ai_action": dec_result.ai_recommendation.recommended_action.value,
            "policy_verdict": dec_result.policy_evaluation.verdict.value,
            "gateway_reference": exec_result.gateway_reference_id,
            "recovered_amount_formatted": f"₹{verif_res.recovered_amount_cents / 100:.2f}",
            "net_recovery_formatted": f"₹{verif_res.net_recovery_cents / 100:.2f}",
            "final_status": verif_res.case_status.value,
        }

    elif request.scenario_id == "scenario_2":
        # SCENARIO 2: Bank Outage Cooldown
        order = OrderModel(
            merchant_id=merchant.id,
            external_order_id=f"ord_sc2_{uuid.uuid4().hex[:6]}",
            amount_cents=1200000,  # ₹12,000.00
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        db.add(order)
        await db.flush()

        init_payment = PaymentModel(
            merchant_id=merchant.id,
            order_id=order.id,
            external_payment_id=f"pay_init_{uuid.uuid4().hex[:6]}",
            amount_cents=1200000,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code="GATEWAY_ERROR",
            error_description="HDFC Bank UPI gateway unreachable (503 Service Unavailable)",
        )
        db.add(init_payment)
        await db.flush()

        case = RecoveryCaseModel(
            merchant_id=merchant.id,
            order_id=order.id,
            initial_payment_id=init_payment.id,
            amount_at_risk_cents=1200000,
            amount_recovered_cents=0,
            currency="INR",
            status=RecoveryCaseStatus.DIAGNOSING,
            failure_category=FailureCategory.BANK_SYSTEM_OUTAGE,
            is_transient=True,
            diagnosis_reasoning="Issuing bank system outage detected. Immediate retries will fail.",
            current_attempt_count=0,
            max_allowed_attempts=3,
            deadline_at=now + timedelta(hours=72),
        )
        db.add(case)
        await db.flush()

        ai_adapter = MockStrategyAIAdapter(
            force_action=RecoveryActionType.WAIT_AND_REASSESS,
            force_confidence=0.96,
            force_diagnosis="Bank server failure is transient.",
            force_rationale="Enforcing 30-minute cooldown period.",
        )
        enrichment_ctx = CaseEnrichmentContext(customer=None)

        dec_result = await AIDecisionService.evaluate_with_ai(
            session=db,
            case=case,
            context=enrichment_ctx,
            policy=MerchantPolicySnapshot(),
            ai_client=ai_adapter,
        )

        cmd = dec_result.authorized_command
        if not cmd:
            cmd = RecoveryCommand.create(
                case_id=case.id,
                merchant_id=merchant.id,
                order_id=order.id,
                action_type=dec_result.policy_evaluation.authorized_action,
                attempt_number=1,
                amount_cents=case.amount_at_risk_cents,
                currency=case.currency,
                deadline_at=case.deadline_at,
                payload={"reassessment_delay_seconds": 1800},
            )

        exec_result = await ActionOrchestrator.execute_command(
            session=db,
            command=cmd,
            decision_id=dec_result.decision_record_id,
            gateway=mock_gateway,
        )
        await db.commit()

        return {
            "scenario": "scenario_2",
            "title": "Scenario 2: Bank Outage Cooldown",
            "case_id": str(case.id),
            "order_id": order.external_order_id,
            "amount_formatted": "₹12,000.00",
            "ai_action": dec_result.ai_recommendation.recommended_action.value,
            "policy_verdict": dec_result.policy_evaluation.verdict.value,
            "final_status": exec_result.case_status.value,
            "scheduled_reassessment": case.next_action_scheduled_at.isoformat()
            if case.next_action_scheduled_at
            else None,
        }

    elif request.scenario_id == "scenario_3":
        # SCENARIO 3: High Value Policy Override
        order = OrderModel(
            merchant_id=merchant.id,
            external_order_id=f"ord_sc3_{uuid.uuid4().hex[:6]}",
            amount_cents=8500000,  # ₹85,000.00 (Exceeds ₹50,000 policy threshold)
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        db.add(order)
        await db.flush()

        init_payment = PaymentModel(
            merchant_id=merchant.id,
            order_id=order.id,
            external_payment_id=f"pay_init_{uuid.uuid4().hex[:6]}",
            amount_cents=8500000,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code="PAYMENT_LIMIT_EXCEEDED",
            error_description="Transaction limit exceeded on corporate card",
        )
        db.add(init_payment)
        await db.flush()

        case = RecoveryCaseModel(
            merchant_id=merchant.id,
            order_id=order.id,
            initial_payment_id=init_payment.id,
            amount_at_risk_cents=8500000,
            amount_recovered_cents=0,
            currency="INR",
            status=RecoveryCaseStatus.DIAGNOSING,
            failure_category=FailureCategory.INSUFFICIENT_FUNDS,
            is_transient=False,
            diagnosis_reasoning="High-value corporate payment ₹85,000.00 requires white-glove manual assistance.",
            current_attempt_count=0,
            max_allowed_attempts=2,
            deadline_at=now + timedelta(hours=72),
        )
        db.add(case)
        await db.flush()

        ai_adapter = MockStrategyAIAdapter(
            force_action=RecoveryActionType.PAYMENT_LINK,
            force_confidence=0.88,
            force_diagnosis="Customer exceeded limit on card.",
            force_rationale="Send customized payment link with alternative corporate payment methods.",
        )
        enrichment_ctx = CaseEnrichmentContext(customer=None)

        dec_result = await AIDecisionService.evaluate_with_ai(
            session=db,
            case=case,
            context=enrichment_ctx,
            policy=MerchantPolicySnapshot(high_value_escalation_threshold_cents=5000000),
            ai_client=ai_adapter,
        )

        await db.commit()

        return {
            "scenario": "scenario_3",
            "title": "Scenario 3: High-Value Policy Override",
            "case_id": str(case.id),
            "order_id": order.external_order_id,
            "amount_formatted": "₹85,000.00",
            "ai_action": dec_result.ai_recommendation.recommended_action.value,
            "policy_verdict": dec_result.policy_evaluation.verdict.value,
            "authorized_action": dec_result.policy_evaluation.authorized_action.value,
            "rule_triggered": dec_result.policy_evaluation.rule_code,
            "final_status": case.status.value,
        }

    elif request.scenario_id == "scenario_4":
        # SCENARIO 4: AI Failure Fallback to Deterministic ERV
        order = OrderModel(
            merchant_id=merchant.id,
            external_order_id=f"ord_sc4_{uuid.uuid4().hex[:6]}",
            amount_cents=320000,  # ₹3,200.00
            currency="INR",
            status=OrderStatus.ATTEMPTED,
        )
        db.add(order)
        await db.flush()

        init_payment = PaymentModel(
            merchant_id=merchant.id,
            order_id=order.id,
            external_payment_id=f"pay_init_{uuid.uuid4().hex[:6]}",
            amount_cents=320000,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code="USER_CANCELLED",
            error_description="Customer cancelled 3DS page",
        )
        db.add(init_payment)
        await db.flush()

        case = RecoveryCaseModel(
            merchant_id=merchant.id,
            order_id=order.id,
            initial_payment_id=init_payment.id,
            amount_at_risk_cents=320000,
            amount_recovered_cents=0,
            currency="INR",
            status=RecoveryCaseStatus.DIAGNOSING,
            failure_category=FailureCategory.USER_AUTHENTICATION_DROPOFF,
            is_transient=False,
            diagnosis_reasoning="3DS cancellation. Fallback to deterministic ERV ranker when AI is offline.",
            current_attempt_count=0,
            max_allowed_attempts=2,
            deadline_at=now + timedelta(hours=72),
        )
        db.add(case)
        await db.flush()

        # AI Adapter that simulates Timeout / Outage
        ai_timeout_adapter = MockStrategyAIAdapter(should_timeout=True)
        enrichment_ctx = CaseEnrichmentContext(customer=None)

        dec_result = await AIDecisionService.evaluate_with_ai(
            session=db,
            case=case,
            context=enrichment_ctx,
            policy=MerchantPolicySnapshot(),
            ai_client=ai_timeout_adapter,
        )

        cmd = dec_result.authorized_command
        if not cmd:
            cmd = RecoveryCommand.create(
                case_id=case.id,
                merchant_id=merchant.id,
                order_id=order.id,
                action_type=dec_result.policy_evaluation.authorized_action,
                attempt_number=1,
                amount_cents=case.amount_at_risk_cents,
                currency=case.currency,
                deadline_at=case.deadline_at,
            )

        exec_result = await ActionOrchestrator.execute_command(
            session=db,
            command=cmd,
            decision_id=dec_result.decision_record_id,
            gateway=mock_gateway,
        )
        await db.commit()

        return {
            "scenario": "scenario_4",
            "title": "Scenario 4: AI Failure Fallback to Deterministic ERV",
            "case_id": str(case.id),
            "order_id": order.external_order_id,
            "amount_formatted": "₹3,200.00",
            "ai_action": dec_result.ai_recommendation.recommended_action.value,
            "policy_verdict": dec_result.policy_evaluation.verdict.value,
            "authorized_action": dec_result.policy_evaluation.authorized_action.value,
            "ai_reasoning": dec_result.ai_recommendation.rationale,
            "final_status": exec_result.case_status.value,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario ID: {request.scenario_id}")


@router.post("/seed-cohort", summary="Seed Controlled Demo Cohort (22 Cases)")
async def seed_demo_cohort_endpoint(
    merchant_slug: str = Query("demo-store", description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Seeds a controlled cohort of 22 realistic demo recovery cases:
    - 5 Authentication dropoffs
    - 5 Bank outages
    - 5 Insufficient funds
    - 3 Permanent declines
    - 2 Fraud risk blocks
    - 2 High-value transaction failures

    All entities are strictly tagged as DEMO/SYNTHETIC in metadata_json.
    """
    merchant = await get_or_create_demo_merchant(db, merchant_slug)
    now = datetime.now(timezone.utc)
    mock_ai = MockStrategyAIAdapter()
    policy = MerchantPolicySnapshot()

    # Cohort blueprint definition (category, amount_cents, risk_score, count, label)
    cohort_specs = [
        (FailureCategory.USER_AUTHENTICATION_DROPOFF, 450000, 0.15, 5, "Auth Dropoff"),
        (FailureCategory.BANK_SYSTEM_OUTAGE, 350000, 0.20, 5, "Bank Outage"),
        (FailureCategory.INSUFFICIENT_FUNDS, 250000, 0.40, 5, "Insufficient Funds"),
        (FailureCategory.PERMANENT_INSTRUMENT_DECLINE, 600000, 0.50, 3, "Permanent Decline"),
        (FailureCategory.FRAUD_RISK_BLOCK, 1200000, 0.95, 2, "Fraud Block"),
        (FailureCategory.USER_AUTHENTICATION_DROPOFF, 7500000, 0.20, 2, "High-Value Order"),
    ]

    seeded_cases = []
    case_counter = 1

    for cat, amount, risk, count, label in cohort_specs:
        for i in range(count):
            uid_hex = uuid.uuid4().hex[:8]
            customer = CustomerModel(
                merchant_id=merchant.id,
                external_customer_id=f"demo_cust_{uid_hex}",
                email=f"demo.customer.{uid_hex}@example.com",
                phone=f"+9198{i:02d}000{case_counter:03d}",
                name=f"Demo Customer {case_counter}",
                risk_score=risk,
                recovery_success_count=2 if risk < 0.3 else 0,
                total_failure_count=1 if risk < 0.5 else 4,
            )
            db.add(customer)
            await db.flush()

            order = OrderModel(
                merchant_id=merchant.id,
                customer_id=customer.id,
                external_order_id=f"order_demo_{uid_hex}",
                amount_cents=amount,
                currency="INR",
                status=OrderStatus.ATTEMPTED,
            )
            db.add(order)
            await db.flush()

            payment = PaymentModel(
                merchant_id=merchant.id,
                order_id=order.id,
                customer_id=customer.id,
                external_payment_id=f"pay_demo_{uid_hex}",
                amount_cents=amount,
                currency="INR",
                status=PaymentStatus.FAILED,
                method="card" if "Permanent" in label else "upi",
                error_code="BAD_REQUEST_ERROR" if "Auth" in label else "GATEWAY_ERROR",
                error_description=f"Synthetic demo failure: {label}",
            )
            db.add(payment)
            await db.flush()

            case = RecoveryCaseModel(
                merchant_id=merchant.id,
                order_id=order.id,
                customer_id=customer.id,
                initial_payment_id=payment.id,
                amount_at_risk_cents=amount,
                amount_recovered_cents=0,
                currency="INR",
                status=RecoveryCaseStatus.DIAGNOSING,
                failure_category=cat,
                is_transient=cat
                in (FailureCategory.BANK_SYSTEM_OUTAGE, FailureCategory.TECHNICAL_GATEWAY_TIMEOUT),
                diagnosis_reasoning=f"Evaluator Demo Cohort - {label} #{i + 1}",
                current_attempt_count=0,
                max_allowed_attempts=2,
                deadline_at=now + timedelta(hours=72),
                metadata_json={
                    "is_demo": True,
                    "is_synthetic": True,
                    "cohort": "evaluator_demo_cohort",
                    "label": label,
                    "case_number": case_counter,
                },
            )
            db.add(case)
            await db.flush()

            # Run decision pipeline on seeded case
            enrichment_ctx = CaseEnrichmentContext(
                customer=CustomerSnapshot(
                    id=customer.id,
                    merchant_id=merchant.id,
                    external_customer_id=customer.external_customer_id,
                    email=customer.email,
                    phone=customer.phone,
                    name=customer.name,
                    risk_score=RiskScore(score=risk),
                    recovery_success_count=customer.recovery_success_count,
                    total_failure_count=customer.total_failure_count,
                ),
            )

            dec_result = await AIDecisionService.evaluate_with_ai(
                session=db,
                case=case,
                context=enrichment_ctx,
                policy=policy,
                ai_client=mock_ai,
            )

            seeded_cases.append(
                {
                    "case_number": case_counter,
                    "case_id": str(case.id),
                    "label": label,
                    "failure_category": cat.value,
                    "amount_paise": amount,
                    "amount_formatted": f"₹{amount / 100:.2f}",
                    "policy_verdict": dec_result.policy_evaluation.verdict.value,
                    "recommended_action": dec_result.ai_recommendation.recommended_action.value,
                    "authorized_action": dec_result.policy_evaluation.authorized_action.value,
                }
            )
            case_counter += 1

    await db.commit()

    return {
        "status": "success",
        "merchant_slug": merchant_slug,
        "total_seeded_cases": len(seeded_cases),
        "cohort_breakdown": {
            "authentication_dropoffs": 5,
            "bank_outages": 5,
            "insufficient_funds": 5,
            "permanent_declines": 3,
            "fraud_risk_blocks": 2,
            "high_value_failures": 2,
        },
        "cases": seeded_cases,
    }


@router.post("/reset-and-seed", summary="Safely Reset Demo Records & Seed Clean 22-Case Cohort")
async def reset_and_seed_demo_endpoint(
    merchant_slug: str = Query("demo-store", description="Merchant unique slug identifier"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Safely purges ONLY existing records explicitly tagged as demo/synthetic
    (order_demo_*, demo_cust_*, is_demo=True) without deleting real merchant data,
    then seeds a fresh 22-case evaluation cohort.
    """
    merchant = await get_or_create_demo_merchant(db, merchant_slug)

    # 1. Fetch demo order IDs
    demo_order_stmt = select(OrderModel.id).where(
        OrderModel.merchant_id == merchant.id,
        OrderModel.external_order_id.like("order_demo_%"),
    )
    demo_order_ids = (await db.execute(demo_order_stmt)).scalars().all()

    deleted_cases_count = 0

    if demo_order_ids:
        # Fetch associated demo recovery cases
        demo_case_stmt = select(RecoveryCaseModel.id).where(
            RecoveryCaseModel.merchant_id == merchant.id,
            RecoveryCaseModel.order_id.in_(demo_order_ids),
        )
        demo_case_ids = (await db.execute(demo_case_stmt)).scalars().all()
        deleted_cases_count = len(demo_case_ids)

        if demo_case_ids:
            # Delete dependent outcomes, attempts, decisions for demo cases only
            await db.execute(
                delete(RecoveryOutcomeModel).where(RecoveryOutcomeModel.case_id.in_(demo_case_ids))
            )
            await db.execute(
                delete(RecoveryAttemptModel).where(RecoveryAttemptModel.case_id.in_(demo_case_ids))
            )
            await db.execute(
                delete(RecoveryDecisionModel).where(
                    RecoveryDecisionModel.case_id.in_(demo_case_ids)
                )
            )
            await db.execute(
                delete(RecoveryCaseModel).where(RecoveryCaseModel.id.in_(demo_case_ids))
            )

        # Delete demo payments and orders
        await db.execute(
            delete(PaymentModel).where(
                PaymentModel.merchant_id == merchant.id,
                PaymentModel.order_id.in_(demo_order_ids),
            )
        )
        await db.execute(
            delete(OrderModel).where(
                OrderModel.merchant_id == merchant.id,
                OrderModel.id.in_(demo_order_ids),
            )
        )

    # Delete demo customers with strict prefix match
    await db.execute(
        delete(CustomerModel).where(
            CustomerModel.merchant_id == merchant.id,
            CustomerModel.external_customer_id.like("demo_cust_%"),
        )
    )
    await db.flush()

    # 2. Re-seed the clean cohort
    seed_result = await seed_demo_cohort_endpoint(merchant_slug=merchant_slug, db=db)

    return {
        "status": "reset_and_seeded_successfully",
        "merchant_slug": merchant_slug,
        "purged_demo_cases_count": deleted_cases_count,
        "total_seeded_cases": seed_result["total_seeded_cases"],
        "cohort_breakdown": seed_result["cohort_breakdown"],
        "cases": seed_result["cases"],
    }
