"""Service for managing the creation and lifecycle initiation of RecoveryCase aggregates."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.razorpay.webhooks import ParsedRazorpayPaymentPayload
from packages.domain.enums import RecoveryCaseStatus
from packages.domain.state_machine import CaseStateMachine
from packages.persistence.audit_ledger import AuditLedgerService
from packages.persistence.models.customer import CustomerModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_case import RecoveryCaseModel

logger = logging.getLogger(__name__)

DEFAULT_RECOVERY_WINDOW_HOURS = 72


class CaseCreationService:
    """
    Coordinates creation and initialization of RecoveryCase aggregates.
    Guarantees that only ONE active recovery case exists per order.
    """

    @classmethod
    async def get_active_case_for_order(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> Optional[RecoveryCaseModel]:
        """Finds any non-terminal active recovery case for an order."""
        stmt = (
            select(RecoveryCaseModel)
            .where(
                RecoveryCaseModel.merchant_id == merchant_id,
                RecoveryCaseModel.order_id == order_id,
                RecoveryCaseModel.status.not_in(
                    [
                        RecoveryCaseStatus.RECOVERED,
                        RecoveryCaseStatus.UNRECOVERABLE,
                        RecoveryCaseStatus.EXPIRED,
                        RecoveryCaseStatus.STOPPED,
                    ]
                ),
            )
            .with_for_update()
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @classmethod
    async def create_or_update_recovery_case(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        order: OrderModel,
        payment: PaymentModel,
        customer: Optional[CustomerModel],
        payload: ParsedRazorpayPaymentPayload,
        enrichment_context: Dict[str, Any],
    ) -> Tuple[RecoveryCaseModel, bool]:
        """
        Creates or updates a RecoveryCase aggregate.
        Enforces domain state machine transitions: DETECTED -> ENRICHING -> DIAGNOSING.

        Returns: (case: RecoveryCaseModel, is_new: bool)
        """
        existing_case = await cls.get_active_case_for_order(session, merchant_id, order.id)

        now = datetime.now(timezone.utc)

        if existing_case is not None:
            logger.info(
                f"Active recovery case '{existing_case.id}' already exists for order '{order.external_order_id}'. Updating diagnostics."
            )
            # Update latest payment failure info
            existing_case.initial_payment_id = payment.id
            existing_case.failure_category = payload.failure_category.value
            existing_case.is_transient = payload.is_transient_failure
            existing_case.diagnosis_reasoning = payload.error_description or payload.error_reason

            # Update metadata
            meta = dict(existing_case.metadata_json or {})
            meta["latest_payment_id"] = payment.external_payment_id
            meta["enrichment_context"] = enrichment_context
            existing_case.metadata_json = meta

            await session.flush()

            # Record audit trail
            await AuditLedgerService.record_event(
                session=session,
                merchant_id=merchant_id,
                entity_type="RECOVERY_CASE",
                entity_id=existing_case.id,
                action="PAYMENT_FAILURE_APPENDED",
                actor_type="SYSTEM",
                actor_id="case-creation-service",
                payload={
                    "order_id": str(order.id),
                    "payment_id": str(payment.id),
                    "failure_category": payload.failure_category.value,
                },
            )

            return existing_case, False

        # --- Create New RecoveryCase Aggregate ---
        deadline = now + timedelta(hours=DEFAULT_RECOVERY_WINDOW_HOURS)

        # 1. State Machine: Initialize at DETECTED
        initial_status = RecoveryCaseStatus.DETECTED

        recovery_case = RecoveryCaseModel(
            merchant_id=merchant_id,
            order_id=order.id,
            initial_payment_id=payment.id,
            customer_id=customer.id if customer else None,
            amount_at_risk_cents=payment.amount_cents,
            currency=payment.currency,
            status=initial_status,
            failure_category=payload.failure_category.value,
            is_transient=payload.is_transient_failure,
            diagnosis_reasoning=payload.error_description or payload.error_reason,
            current_attempt_count=0,
            max_allowed_attempts=2,
            deadline_at=deadline,
            metadata_json={
                "originating_event_id": payload.event_id,
                "gateway_method": payload.method,
                "enrichment_context": enrichment_context,
            },
        )
        session.add(recovery_case)
        await session.flush()

        logger.info(
            f"Created RecoveryCase '{recovery_case.id}' for order '{order.external_order_id}' (Amount: ₹{recovery_case.amount_at_risk_cents / 100:.2f})."
        )

        # 2. State Machine: DETECTED -> ENRICHING
        CaseStateMachine.validate_transition(recovery_case.status, RecoveryCaseStatus.ENRICHING)
        recovery_case.status = RecoveryCaseStatus.ENRICHING
        await session.flush()

        # 3. State Machine: ENRICHING -> DIAGNOSING
        CaseStateMachine.validate_transition(recovery_case.status, RecoveryCaseStatus.DIAGNOSING)
        recovery_case.status = RecoveryCaseStatus.DIAGNOSING
        await session.flush()

        # 4. Append Tamper-Evident Audit Event
        await AuditLedgerService.record_event(
            session=session,
            merchant_id=merchant_id,
            entity_type="RECOVERY_CASE",
            entity_id=recovery_case.id,
            action="RECOVERY_CASE_CREATED",
            actor_type="SYSTEM",
            actor_id="case-creation-service",
            payload={
                "order_id": str(order.id),
                "external_order_id": order.external_order_id,
                "payment_id": str(payment.id),
                "external_payment_id": payment.external_payment_id,
                "amount_at_risk_cents": recovery_case.amount_at_risk_cents,
                "failure_category": payload.failure_category.value,
                "is_transient": payload.is_transient_failure,
                "status": recovery_case.status.value,
            },
        )

        return recovery_case, True
