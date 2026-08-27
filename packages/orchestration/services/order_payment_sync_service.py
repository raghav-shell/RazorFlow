"""Service for synchronizing Order, Payment, and Customer state from gateway events."""

import logging
import uuid
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.razorpay.webhooks import ParsedRazorpayPaymentPayload
from packages.domain.enums import OrderStatus, PaymentStatus
from packages.persistence.models.customer import CustomerModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel

logger = logging.getLogger(__name__)


class OrderPaymentSyncService:
    """
    Synchronizes Customer, Order, and Payment records in the database with strict
    state-transition guards to prevent out-of-order webhook degradation.
    """

    @classmethod
    async def sync_customer(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        payload: ParsedRazorpayPaymentPayload,
    ) -> Optional[CustomerModel]:
        """Upserts customer based on email or phone identifier within merchant boundary."""
        email = payload.customer_email.strip().lower() if payload.customer_email else None
        phone = payload.customer_contact.strip() if payload.customer_contact else None

        if not email and not phone:
            return None

        # Look up existing customer
        query = select(CustomerModel).where(CustomerModel.merchant_id == merchant_id)
        if email and phone:
            query = query.where((CustomerModel.email == email) | (CustomerModel.phone == phone))
        elif email:
            query = query.where(CustomerModel.email == email)
        else:
            query = query.where(CustomerModel.phone == phone)

        customer = (await session.execute(query)).scalars().first()

        if customer is None:
            customer = CustomerModel(
                merchant_id=merchant_id,
                email=email,
                phone=phone,
                name=payload.customer_name or "Customer",
                risk_score=0.0,
                recovery_success_count=0,
                total_failure_count=1 if payload.status == "failed" else 0,
            )
            session.add(customer)
            await session.flush()
        else:
            # Update customer counters
            if payload.status == "failed":
                customer.total_failure_count += 1
            if payload.customer_name and customer.name in ("Customer", None):
                customer.name = payload.customer_name
            await session.flush()

        return customer

    @classmethod
    async def sync_order(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        payload: ParsedRazorpayPaymentPayload,
    ) -> OrderModel:
        """
        Upserts Order record. Guarantees that a PAID order is never downgraded by late events.
        """
        external_order_id = (
            payload.external_order_id or f"order_synth_{payload.external_payment_id}"
        )

        stmt = (
            select(OrderModel)
            .where(
                OrderModel.merchant_id == merchant_id,
                OrderModel.external_order_id == external_order_id,
            )
            .with_for_update()
        )

        order = (await session.execute(stmt)).scalar_one_or_none()

        is_captured_event = payload.status in ("captured", "authorized") and payload.event_type in (
            "payment.captured",
            "payment.authorized",
            "order.paid",
        )
        new_order_status = OrderStatus.PAID if is_captured_event else OrderStatus.ATTEMPTED

        if order is None:
            order = OrderModel(
                merchant_id=merchant_id,
                customer_id=customer_id,
                external_order_id=external_order_id,
                amount_cents=payload.amount_cents,
                currency=payload.currency,
                status=new_order_status,
                receipt=payload.description,
            )
            session.add(order)
            await session.flush()
            logger.info(
                f"Created order '{external_order_id}' with status {new_order_status.value}."
            )
        else:
            # Enforce non-downgrade invariant
            if order.status == OrderStatus.PAID:
                logger.info(
                    f"Order '{external_order_id}' is already PAID. Preserving PAID status despite event '{payload.event_type}'."
                )
            else:
                order.status = new_order_status
                if customer_id and not order.customer_id:
                    order.customer_id = customer_id
                await session.flush()

        return order

    @classmethod
    async def sync_payment(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        order_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        payload: ParsedRazorpayPaymentPayload,
    ) -> Tuple[PaymentModel, bool]:
        """
        Upserts Payment record. Guarantees that a CAPTURED payment is not downgraded to FAILED.
        Returns: (payment: PaymentModel, is_new: bool)
        """
        stmt = (
            select(PaymentModel)
            .where(
                PaymentModel.merchant_id == merchant_id,
                PaymentModel.external_payment_id == payload.external_payment_id,
            )
            .with_for_update()
        )

        payment = (await session.execute(stmt)).scalar_one_or_none()

        status_mapping = {
            "failed": PaymentStatus.FAILED,
            "captured": PaymentStatus.CAPTURED,
            "authorized": PaymentStatus.AUTHORIZED,
            "refunded": PaymentStatus.REFUNDED,
        }
        mapped_status = status_mapping.get(payload.status.lower(), PaymentStatus.FAILED)

        if payment is None:
            payment = PaymentModel(
                merchant_id=merchant_id,
                order_id=order_id,
                customer_id=customer_id,
                external_payment_id=payload.external_payment_id,
                amount_cents=payload.amount_cents,
                currency=payload.currency,
                status=mapped_status,
                method=payload.method,
                error_code=payload.error_code,
                error_description=payload.error_description,
                error_source=payload.error_source,
                error_step=payload.error_step,
                error_reason=payload.error_reason,
                rzp_created_at=payload.created_at_timestamp,
            )
            session.add(payment)
            await session.flush()
            logger.info(
                f"Created payment '{payload.external_payment_id}' with status {mapped_status.value}."
            )
            return payment, True
        else:
            # Enforce non-downgrade invariant for payments
            if payment.status == PaymentStatus.CAPTURED and mapped_status == PaymentStatus.FAILED:
                logger.warning(
                    f"Ignored out-of-order failed event for already CAPTURED payment '{payload.external_payment_id}'."
                )
            else:
                payment.status = mapped_status
                payment.error_code = payload.error_code
                payment.error_description = payload.error_description
                payment.error_source = payload.error_source
                payment.error_step = payload.error_step
                payment.error_reason = payload.error_reason
                await session.flush()

            return payment, False
