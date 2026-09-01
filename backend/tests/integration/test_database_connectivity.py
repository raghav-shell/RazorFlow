"""Integration tests verifying SQLAlchemy ORM model persistence, relationships, and queries."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.domain.enums import (
    OrderStatus,
    PaymentStatus,
    RecoveryCaseStatus,
)
from packages.persistence.database import check_database_health
from packages.persistence.models import (
    CustomerModel,
    MerchantModel,
    MerchantProviderConfigModel,
    OrderModel,
    PaymentModel,
    RecoveryCaseModel,
)


@pytest.mark.asyncio
async def test_database_healthcheck_helper(async_db_session: AsyncSession):
    is_healthy = await check_database_health(async_db_session)
    assert is_healthy is True


@pytest.mark.asyncio
async def test_merchant_and_config_persistence(async_db_session: AsyncSession):
    merchant = MerchantModel(
        name="Acme Superstore",
        slug="acme-superstore",
        currency="INR",
    )
    async_db_session.add(merchant)
    await async_db_session.flush()

    config = MerchantProviderConfigModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        key_id="rzp_test_key_123",
        key_secret_enc="enc_secret_456",
        webhook_secret_enc="enc_wh_sec_789",
        is_test_mode=True,
    )
    async_db_session.add(config)
    await async_db_session.commit()

    # Query back with eager loading
    stmt = (
        select(MerchantModel)
        .options(selectinload(MerchantModel.provider_configs))
        .where(MerchantModel.slug == "acme-superstore")
    )
    result = await async_db_session.execute(stmt)
    persisted_merchant = result.scalar_one()

    assert persisted_merchant is not None
    assert persisted_merchant.name == "Acme Superstore"
    assert len(persisted_merchant.provider_configs) == 1
    assert persisted_merchant.provider_configs[0].key_id == "rzp_test_key_123"


@pytest.mark.asyncio
async def test_order_payment_and_case_relational_graph(async_db_session: AsyncSession):
    merchant_id = uuid.uuid4()
    merchant = MerchantModel(
        id=merchant_id, name="Test Merchant", slug=f"test-merchant-{uuid.uuid4().hex[:6]}"
    )
    async_db_session.add(merchant)
    await async_db_session.flush()

    customer = CustomerModel(
        merchant_id=merchant_id,
        external_customer_id="cust_001",
        email="gaurav@example.com",
        phone="+919876543210",
        name="Gaurav Kumar",
    )
    async_db_session.add(customer)
    await async_db_session.flush()

    order = OrderModel(
        merchant_id=merchant_id,
        customer_id=customer.id,
        external_order_id="order_test_999",
        amount_cents=500000,  # ₹5,000.00
        currency="INR",
        status=OrderStatus.ATTEMPTED,
    )
    async_db_session.add(order)
    await async_db_session.flush()

    payment = PaymentModel(
        merchant_id=merchant_id,
        order_id=order.id,
        customer_id=customer.id,
        external_payment_id="pay_test_888",
        amount_cents=500000,
        currency="INR",
        status=PaymentStatus.FAILED,
        error_code="BAD_REQUEST_PAYMENT_TIMED_OUT",
        error_description="Payment attempt timed out at issuing bank",
        error_source="bank",
        error_step="payment_authorization",
    )
    async_db_session.add(payment)
    await async_db_session.flush()

    recovery_case = RecoveryCaseModel(
        merchant_id=merchant_id,
        order_id=order.id,
        initial_payment_id=payment.id,
        customer_id=customer.id,
        amount_at_risk_cents=500000,
        currency="INR",
        status=RecoveryCaseStatus.DETECTED,
        failure_category="TECHNICAL_GATEWAY_TIMEOUT",
        is_transient=True,
        deadline_at=datetime.now(timezone.utc),
    )
    async_db_session.add(recovery_case)
    await async_db_session.commit()

    # Query back RecoveryCase and verify relationships
    stmt = (
        select(RecoveryCaseModel)
        .options(
            selectinload(RecoveryCaseModel.order),
            selectinload(RecoveryCaseModel.merchant),
        )
        .where(RecoveryCaseModel.order_id == order.id)
    )
    result = await async_db_session.execute(stmt)
    persisted_case = result.scalar_one()

    assert persisted_case.amount_at_risk_cents == 500000
    assert persisted_case.status == RecoveryCaseStatus.DETECTED
    assert persisted_case.failure_category == "TECHNICAL_GATEWAY_TIMEOUT"
    assert persisted_case.order.external_order_id == "order_test_999"
    assert persisted_case.merchant.name == "Test Merchant"
