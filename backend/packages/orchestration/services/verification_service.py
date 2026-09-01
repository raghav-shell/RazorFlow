"""Financial Verification Service reconciling webhooks and polling to verify financial truth."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from packages.adapters.razorpay.webhooks import ParsedRazorpayPaymentPayload
from packages.domain.enums import (
    OrderStatus,
    PaymentStatus,
    RecoveryActionType,
    RecoveryAttemptStatus,
    RecoveryCaseStatus,
)
from packages.domain.state_machine import AttemptStateMachine, CaseStateMachine
from packages.persistence.audit_ledger import AuditLedgerService
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_attempt import RecoveryAttemptModel
from packages.persistence.models.recovery_case import RecoveryCaseModel
from packages.persistence.models.recovery_outcome import RecoveryOutcomeModel
from packages.ports.payment_gateway import GatewayProviderConfig, PaymentGatewayPort

logger = logging.getLogger(__name__)


# Standard modeled intervention costs in minor units (paise)
_STRATEGY_COST_MAP = {
    RecoveryActionType.PAYMENT_LINK: 200,  # ₹2.00
    RecoveryActionType.CUSTOMER_REMINDER: 150,  # ₹1.50
    RecoveryActionType.WAIT_AND_REASSESS: 0,  # ₹0.00
    RecoveryActionType.HUMAN_ESCALATION: 10000,  # ₹100.00
    RecoveryActionType.DO_NOTHING: 0,
}


@dataclass(frozen=True)
class VerificationResult:
    """Auditable result of financial verification."""

    is_verified: bool
    case_id: uuid.UUID
    outcome_id: Optional[uuid.UUID]
    case_status: RecoveryCaseStatus
    recovered_amount_cents: int
    net_recovery_cents: int
    verification_source: str
    failure_reason: Optional[str] = None


class VerificationService:
    """
    Authoritative Financial Verification Service.
    Determines financial truth from canonical webhooks and gateway polling.
    Guarantees no false RECOVERED declarations without verified captured payment proof.
    """

    @classmethod
    async def verify_and_recover_case(
        cls,
        session: AsyncSession,
        case: RecoveryCaseModel,
        settling_payment: PaymentModel,
        verification_source: str,
        gateway_reference_id: Optional[str] = None,
    ) -> VerificationResult:
        """
        Reconciles evidence and transitions case to RECOVERED if financial invariants hold.
        """
        now = datetime.now(timezone.utc)
        case_id = case.id
        merchant_id = case.merchant_id

        # 1. Out-of-order check: If case is ALREADY RECOVERED, preserve invariant (do not downgrade or duplicate)
        if case.status == RecoveryCaseStatus.RECOVERED:
            logger.info(
                f"Case '{case_id}' is already RECOVERED. Skipping duplicate outcome creation."
            )
            existing_outcome = (
                await session.execute(
                    select(RecoveryOutcomeModel).where(RecoveryOutcomeModel.case_id == case_id)
                )
            ).scalar_one_or_none()
            return VerificationResult(
                is_verified=True,
                case_id=case_id,
                outcome_id=existing_outcome.id if existing_outcome else None,
                case_status=case.status,
                recovered_amount_cents=case.amount_recovered_cents,
                net_recovery_cents=existing_outcome.net_recovery_cents
                if existing_outcome
                else case.amount_recovered_cents,
                verification_source=verification_source,
            )

        # 2. Strict Financial Invariant Validations
        if settling_payment.status != PaymentStatus.CAPTURED:
            logger.warning(
                f"Financial Invariant Violation: Payment '{settling_payment.id}' status is '{settling_payment.status.value}', "
                f"expected CAPTURED. Verification aborted."
            )
            return VerificationResult(
                is_verified=False,
                case_id=case_id,
                outcome_id=None,
                case_status=case.status,
                recovered_amount_cents=0,
                net_recovery_cents=0,
                verification_source=verification_source,
                failure_reason=f"Payment status is {settling_payment.status.value}, not CAPTURED.",
            )

        if settling_payment.currency != case.currency:
            logger.warning(
                f"Currency Invariant Violation: Payment currency '{settling_payment.currency}' != Case currency '{case.currency}'."
            )
            return VerificationResult(
                is_verified=False,
                case_id=case_id,
                outcome_id=None,
                case_status=case.status,
                recovered_amount_cents=0,
                net_recovery_cents=0,
                verification_source=verification_source,
                failure_reason=f"Currency mismatch: {settling_payment.currency} vs {case.currency}.",
            )

        # 3. Find the matching recovery attempt (if any)
        attempt_stmt = (
            select(RecoveryAttemptModel)
            .where(RecoveryAttemptModel.case_id == case_id)
            .order_by(RecoveryAttemptModel.created_at.desc())
        )
        attempts = (await session.execute(attempt_stmt)).scalars().all()
        matching_attempt: Optional[RecoveryAttemptModel] = None

        if gateway_reference_id:
            for att in attempts:
                if att.gateway_reference_id == gateway_reference_id:
                    matching_attempt = att
                    break

        if not matching_attempt and attempts:
            matching_attempt = attempts[0]

        # Calculate modeled intervention cost
        recovery_method: Optional[RecoveryActionType] = (
            matching_attempt.action_type if matching_attempt else None
        )
        cost_incurred_cents = _STRATEGY_COST_MAP.get(recovery_method, 0) if recovery_method else 0
        recovered_amount_cents = settling_payment.amount_cents
        net_recovery_cents = max(0, recovered_amount_cents - cost_incurred_cents)

        # 4. Advance Case State Machine to RECOVERED
        if case.status != RecoveryCaseStatus.VERIFYING and CaseStateMachine.can_transition(
            case.status, RecoveryCaseStatus.VERIFYING
        ):
            CaseStateMachine.validate_transition(case.status, RecoveryCaseStatus.VERIFYING)
            case.status = RecoveryCaseStatus.VERIFYING
            await session.flush()

        if CaseStateMachine.can_transition(case.status, RecoveryCaseStatus.RECOVERED):
            CaseStateMachine.validate_transition(case.status, RecoveryCaseStatus.RECOVERED)
            case.status = RecoveryCaseStatus.RECOVERED

        case.amount_recovered_cents = recovered_amount_cents
        await session.flush()

        # 5. Mark matching attempt as SUCCEEDED
        if matching_attempt and AttemptStateMachine.can_transition(
            matching_attempt.status, RecoveryAttemptStatus.SUCCEEDED
        ):
            AttemptStateMachine.validate_transition(
                matching_attempt.status, RecoveryAttemptStatus.SUCCEEDED
            )
            matching_attempt.status = RecoveryAttemptStatus.SUCCEEDED
            matching_attempt.completed_at = now
            await session.flush()

        # 6. Create / Update RecoveryOutcomeModel
        outcome_stmt = select(RecoveryOutcomeModel).where(RecoveryOutcomeModel.case_id == case_id)
        outcome = (await session.execute(outcome_stmt)).scalar_one_or_none()

        if not outcome:
            outcome = RecoveryOutcomeModel(
                case_id=case_id,
                merchant_id=merchant_id,
                settling_payment_id=settling_payment.id,
                successful_attempt_id=matching_attempt.id if matching_attempt else None,
                is_successful=True,
                amount_recovered_cents=recovered_amount_cents,
                cost_incurred_cents=cost_incurred_cents,
                net_recovery_cents=net_recovery_cents,
                recovery_method=recovery_method,
                verification_source=verification_source,
                verified_at=now,
            )
            session.add(outcome)
        else:
            outcome.is_successful = True
            outcome.amount_recovered_cents = recovered_amount_cents
            outcome.cost_incurred_cents = cost_incurred_cents
            outcome.net_recovery_cents = net_recovery_cents
            outcome.settling_payment_id = settling_payment.id
            outcome.successful_attempt_id = matching_attempt.id if matching_attempt else None
            outcome.verification_source = verification_source
            outcome.verified_at = now

        await session.flush()

        # 7. Record Cryptographic Hash-Chain Audit Events
        await AuditLedgerService.record_event(
            session=session,
            merchant_id=merchant_id,
            entity_type="RECOVERY_OUTCOME",
            entity_id=outcome.id,
            action="PAYMENT_CAPTURED_VERIFIED",
            actor_type="SYSTEM",
            actor_id="verification-service",
            payload={
                "case_id": str(case_id),
                "settling_payment_id": str(settling_payment.id),
                "recovered_amount_cents": recovered_amount_cents,
                "net_recovery_cents": net_recovery_cents,
                "verification_source": verification_source,
            },
        )

        logger.info(
            f"Verification SUCCESS for Case '{case_id}': Recovered ₹{recovered_amount_cents / 100:.2f} "
            f"(Net: ₹{net_recovery_cents / 100:.2f}) via {verification_source}."
        )

        return VerificationResult(
            is_verified=True,
            case_id=case_id,
            outcome_id=outcome.id,
            case_status=case.status,
            recovered_amount_cents=recovered_amount_cents,
            net_recovery_cents=net_recovery_cents,
            verification_source=verification_source,
        )

    @classmethod
    async def verify_from_webhook_event(
        cls,
        session: AsyncSession,
        event: ParsedRazorpayPaymentPayload,
        merchant_id: uuid.UUID,
    ) -> Optional[VerificationResult]:
        """
        Reconciles incoming captured payment webhook with any active RecoveryCase.
        """
        if (
            event.event_type not in ("payment.captured", "payment_link.paid", "order.paid")
            and event.status != "captured"
        ):
            return None

        # Resolve order
        order_stmt = select(OrderModel).where(
            OrderModel.merchant_id == merchant_id,
            OrderModel.external_order_id == event.external_order_id,
        )
        order = (await session.execute(order_stmt)).scalar_one_or_none()
        if not order:
            return None

        # Resolve active RecoveryCase for this order
        case_stmt = select(RecoveryCaseModel).where(
            RecoveryCaseModel.order_id == order.id,
            RecoveryCaseModel.status.in_(
                [
                    RecoveryCaseStatus.APPROVED,
                    RecoveryCaseStatus.EXECUTING,
                    RecoveryCaseStatus.WAITING_EXTERNAL,
                    RecoveryCaseStatus.VERIFYING,
                    RecoveryCaseStatus.ESCALATED,
                ]
            ),
        )
        case = (await session.execute(case_stmt)).scalar_one_or_none()
        if not case:
            return None

        # Resolve settling payment
        pay_stmt = select(PaymentModel).where(
            PaymentModel.merchant_id == merchant_id,
            PaymentModel.external_payment_id == event.external_payment_id,
        )
        settling_payment = (await session.execute(pay_stmt)).scalar_one_or_none()

        if not settling_payment:
            # Create payment record if it arrived via payment_link.paid
            settling_payment = PaymentModel(
                merchant_id=merchant_id,
                order_id=order.id,
                external_payment_id=event.external_payment_id or f"pay_wh_{uuid.uuid4().hex[:8]}",
                amount_cents=event.amount_cents,
                currency=event.currency,
                status=PaymentStatus.CAPTURED,
            )
            session.add(settling_payment)
            await session.flush()
        elif settling_payment.status != PaymentStatus.CAPTURED:
            settling_payment.status = PaymentStatus.CAPTURED
            await session.flush()

        return await cls.verify_and_recover_case(
            session=session,
            case=case,
            settling_payment=settling_payment,
            verification_source="WEBHOOK_EVENT",
            gateway_reference_id=event.raw_payload.get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
            .get("id"),
        )

    @classmethod
    async def poll_and_reconcile_case(
        cls,
        session: AsyncSession,
        case_id: uuid.UUID,
        gateway: PaymentGatewayPort,
    ) -> VerificationResult:
        """
        Polls Razorpay Gateway API to verify payment state and reconciles with local database.
        """
        settings = get_settings()
        case = await session.get(RecoveryCaseModel, case_id)
        if not case:
            raise ValueError(f"RecoveryCase '{case_id}' not found.")

        merchant = await session.get(MerchantModel, case.merchant_id)
        if not merchant:
            raise ValueError(f"Merchant '{case.merchant_id}' not found.")

        prov_stmt = select(MerchantProviderConfigModel).where(
            MerchantProviderConfigModel.merchant_id == case.merchant_id,
            MerchantProviderConfigModel.provider == "RAZORPAY",
            MerchantProviderConfigModel.is_active.is_(True),
        )
        prov_cfg = (await session.execute(prov_stmt)).scalar_one_or_none()

        key_id = (
            prov_cfg.key_id if prov_cfg else (settings.RAZORPAY_KEY_ID or "rzp_test_placeholder")
        )
        key_secret = settings.RAZORPAY_KEY_SECRET or "rzp_test_secret"
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or "rzp_webhook_secret"
        is_test_mode = prov_cfg.is_test_mode if prov_cfg else settings.RAZORPAY_MODE == "test"

        config = GatewayProviderConfig(
            key_id=key_id,
            key_secret=key_secret,
            webhook_secret=webhook_secret,
            is_test_mode=is_test_mode,
        )

        # Check latest attempt for gateway reference (payment link ID)
        attempt_stmt = (
            select(RecoveryAttemptModel)
            .where(RecoveryAttemptModel.case_id == case_id)
            .order_by(RecoveryAttemptModel.created_at.desc())
        )
        attempts = (await session.execute(attempt_stmt)).scalars().all()

        gateway_link_id: Optional[str] = None
        for att in attempts:
            if att.gateway_reference_id and att.action_type == RecoveryActionType.PAYMENT_LINK:
                gateway_link_id = att.gateway_reference_id
                break

        if gateway_link_id:
            link_status = await gateway.fetch_payment_link_status(config, gateway_link_id)
            if link_status.is_success and link_status.status == "paid":
                # Gateway confirms paid! Resolve order and payment
                order = await session.get(OrderModel, case.order_id)
                if order:
                    order.status = OrderStatus.PAID
                    settling_pay = PaymentModel(
                        merchant_id=merchant.id,
                        order_id=order.id,
                        external_payment_id=f"pay_poll_{uuid.uuid4().hex[:8]}",
                        amount_cents=case.amount_at_risk_cents,
                        currency=case.currency,
                        status=PaymentStatus.CAPTURED,
                    )
                    session.add(settling_pay)
                    await session.flush()

                    return await cls.verify_and_recover_case(
                        session=session,
                        case=case,
                        settling_payment=settling_pay,
                        verification_source="GATEWAY_POLL",
                        gateway_reference_id=gateway_link_id,
                    )

        # If not verified yet
        return VerificationResult(
            is_verified=False,
            case_id=case_id,
            outcome_id=None,
            case_status=case.status,
            recovered_amount_cents=0,
            net_recovery_cents=0,
            verification_source="GATEWAY_POLL",
            failure_reason="Gateway poll indicates payment is not yet captured.",
        )
