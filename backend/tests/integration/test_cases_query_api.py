"""Integration tests for Recovery Cases query API and multi-tenant isolation."""

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from packages.domain.enums import OrderStatus, PaymentStatus, RecoveryCaseStatus
from packages.persistence.models.merchant import MerchantModel
from packages.persistence.models.order import OrderModel
from packages.persistence.models.payment import PaymentModel
from packages.persistence.models.recovery_case import RecoveryCaseModel


@pytest.mark.asyncio
async def test_cases_query_api_tenant_isolation(
    async_client: AsyncClient, async_db_session: AsyncSession
):
    # 1. Create Merchant A and a RecoveryCase
    merchant_a = MerchantModel(name="Alpha Store", slug="alpha-store", currency="INR")
    async_db_session.add(merchant_a)
    await async_db_session.flush()

    order_a = OrderModel(
        merchant_id=merchant_a.id,
        external_order_id="order_alpha_01",
        amount_cents=100000,
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order_a)
    await async_db_session.flush()

    payment_a = PaymentModel(
        merchant_id=merchant_a.id,
        order_id=order_a.id,
        external_payment_id="pay_alpha_01",
        amount_cents=100000,
        currency="INR",
        status=PaymentStatus.FAILED,
    )
    async_db_session.add(payment_a)
    await async_db_session.flush()

    case_a = RecoveryCaseModel(
        merchant_id=merchant_a.id,
        order_id=order_a.id,
        initial_payment_id=payment_a.id,
        amount_at_risk_cents=100000,
        currency="INR",
        status=RecoveryCaseStatus.DIAGNOSING,
        deadline_at=datetime.now(timezone.utc),
    )
    async_db_session.add(case_a)

    # 2. Create Merchant B
    merchant_b = MerchantModel(name="Beta Store", slug="beta-store", currency="INR")
    async_db_session.add(merchant_b)
    await async_db_session.commit()

    # 3. Query list for Merchant A -> sees 1 case
    res_a = await async_client.get("/api/v1/cases?merchant_slug=alpha-store")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["count"] == 1
    assert data_a["items"][0]["external_order_id"] == "order_alpha_01"

    # 4. Query list for Merchant B -> sees 0 cases
    res_b = await async_client.get("/api/v1/cases?merchant_slug=beta-store")
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["count"] == 0

    # 5. Tenant Isolation Check: Merchant B attempts to fetch Merchant A's case by direct ID
    res_cross_tenant = await async_client.get(f"/api/v1/cases/{case_a.id}?merchant_slug=beta-store")
    # Must return 404 Not Found (zero cross-tenant leak!)
    assert res_cross_tenant.status_code == 404

    # 6. Merchant A fetches its own case -> 200 with full details
    res_own = await async_client.get(f"/api/v1/cases/{case_a.id}?merchant_slug=alpha-store")
    assert res_own.status_code == 200
    detail = res_own.json()
    assert detail["case_id"] == str(case_a.id)
    assert detail["amount_at_risk_cents"] == 100000
    assert detail["amount_at_risk_formatted"] == "₹1000.00"
    assert detail["status"] == "DIAGNOSING"
