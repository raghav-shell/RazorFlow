"""Service for enriching customer transaction history, failure patterns, and risk signals."""

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.enums import PaymentStatus
from packages.persistence.models.customer import CustomerModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel

logger = logging.getLogger(__name__)


class CustomerEnrichmentService:
    """
    Deterministically computes customer behavioral metrics and historical payment profiles.
    Minimizes PII exposure by generating statistical features rather than raw personal details.
    """

    @classmethod
    async def enrich_customer_context(
        cls,
        session: AsyncSession,
        merchant_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
    ) -> Dict[str, Any]:
        """Derives statistical features and transaction history for context enrichment."""
        if customer_id is None:
            return {
                "has_customer_profile": False,
                "total_orders_count": 0,
                "total_payments_count": 0,
                "successful_payments_count": 0,
                "failed_payments_count": 0,
                "historical_recovery_rate": 0.0,
                "customer_risk_tier": "UNKNOWN",
                "calculated_risk_score": 0.50,
            }

        # 1. Fetch customer entity
        customer = await session.get(CustomerModel, customer_id)
        if customer is None:
            return {"has_customer_profile": False}

        # 2. Count total orders
        orders_count_stmt = select(func.count(OrderModel.id)).where(
            OrderModel.merchant_id == merchant_id, OrderModel.customer_id == customer_id
        )
        total_orders = (await session.execute(orders_count_stmt)).scalar() or 0

        # 3. Count successful and failed payments
        payments_stmt = (
            select(
                PaymentModel.status,
                func.count(PaymentModel.id),
            )
            .where(PaymentModel.merchant_id == merchant_id, PaymentModel.customer_id == customer_id)
            .group_by(PaymentModel.status)
        )
        rows = (await session.execute(payments_stmt)).all()
        payment_counts: Dict[PaymentStatus, int] = {row[0]: row[1] for row in rows}

        successful_count = payment_counts.get(PaymentStatus.CAPTURED, 0)
        failed_count = payment_counts.get(PaymentStatus.FAILED, 0)
        total_payments = successful_count + failed_count

        # 4. Calculate Risk Tier & Recovery Rate
        recovery_successes = customer.recovery_success_count
        if failed_count > 0:
            historical_recovery_rate = round(recovery_successes / failed_count, 4)
        else:
            historical_recovery_rate = 1.0 if successful_count > 0 else 0.0

        # Calculate risk score [0.0 = low risk / reliable, 1.0 = high risk / chronic failures]
        if total_payments == 0:
            risk_score = 0.30
            risk_tier = "NEW_CUSTOMER"
        elif successful_count > 0 and failed_count <= 1:
            risk_score = 0.10
            risk_tier = "LOW_RISK_VIP"
        elif successful_count >= failed_count:
            risk_score = 0.35
            risk_tier = "STANDARD"
        else:
            risk_score = 0.75
            risk_tier = "ELEVATED_RISK"

        # Update customer risk score on record
        customer.risk_score = risk_score
        await session.flush()

        return {
            "has_customer_profile": True,
            "total_orders_count": total_orders,
            "total_payments_count": total_payments,
            "successful_payments_count": successful_count,
            "failed_payments_count": failed_count,
            "recovery_success_count": recovery_successes,
            "historical_recovery_rate": historical_recovery_rate,
            "customer_risk_tier": risk_tier,
            "calculated_risk_score": risk_score,
            "masked_customer_name": f"{customer.name.split()[0]} {customer.name.split()[-1][0]}."
            if customer.name and len(customer.name.split()) > 1
            else customer.name,
        }
