"""Integration tests for Order and Payment synchronization and out-of-order event invariants."""

import json
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from packages.adapters.razorpay.webhooks import parse_razorpay_webhook
from packages.domain.enums import OrderStatus, PaymentStatus
from packages.orchestration.services.order_payment_sync_service import OrderPaymentSyncService
from packages.persistence.models.merchant import MerchantModel


@pytest.mark.asyncio
async def test_order_payment_sync_basic_failure(async_db_session: AsyncSession):
    merchant = MerchantModel(name="Grocery Hub", slug=f"grocery-{uuid.uuid4().hex[:6]}")
    async_db_session.add(merchant)
    await async_db_session.flush()

    raw_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_fail_001",
                    "order_id": "order_sync_001",
                    "amount": 120000,
                    "currency": "INR",
                    "status": "failed",
                    "email": "riya@example.com",
                    "contact": "+919876500000",
                    "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
                    "error_source": "bank",
                    "error_step": "payment_authorization",
                }
            }
        },
        "created_at": 1700000000,
    }
    parsed = parse_razorpay_webhook(json.dumps(raw_payload).encode("utf-8"), {})

    customer = await OrderPaymentSyncService.sync_customer(async_db_session, merchant.id, parsed)
    order = await OrderPaymentSyncService.sync_order(
        async_db_session, merchant.id, customer.id if customer else None, parsed
    )
    payment, is_new = await OrderPaymentSyncService.sync_payment(
        async_db_session, merchant.id, order.id, customer.id if customer else None, parsed
    )

    await async_db_session.commit()

    assert customer is not None
    assert customer.email == "riya@example.com"
    assert order.status == OrderStatus.ATTEMPTED
    assert order.amount_cents == 120000
    assert payment.status == PaymentStatus.FAILED
    assert payment.external_payment_id == "pay_fail_001"
    assert is_new is True


@pytest.mark.asyncio
async def test_out_of_order_event_does_not_downgrade_paid_order(async_db_session: AsyncSession):
    """
    Critical Invariant Test:
    If an order was marked PAID by a successful payment, a delayed out-of-order 'payment.failed'
    webhook must NOT downgrade the Order status from PAID to ATTEMPTED!
    """
    merchant = MerchantModel(name="Fashion Hub", slug=f"fashion-{uuid.uuid4().hex[:6]}")
    async_db_session.add(merchant)
    await async_db_session.flush()

    # 1. Order is paid successfully via payment 1
    success_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_success_100",
                    "order_id": "order_invariant_001",
                    "amount": 350000,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
        "created_at": 1700000050,
    }
    parsed_success = parse_razorpay_webhook(json.dumps(success_payload).encode("utf-8"), {})

    order = await OrderPaymentSyncService.sync_order(
        async_db_session, merchant.id, None, parsed_success
    )
    await async_db_session.commit()
    assert order.status == OrderStatus.PAID

    # 2. Delayed 'payment.failed' webhook arrives for an earlier attempt on the same order
    delayed_fail_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_earlier_fail_090",
                    "order_id": "order_invariant_001",
                    "amount": 350000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
        "created_at": 1700000010,  # Older timestamp
    }
    parsed_delayed_fail = parse_razorpay_webhook(
        json.dumps(delayed_fail_payload).encode("utf-8"), {}
    )

    order_after_delayed_event = await OrderPaymentSyncService.sync_order(
        async_db_session, merchant.id, None, parsed_delayed_fail
    )
    await async_db_session.commit()

    # Invariant: Order MUST remain PAID!
    assert order_after_delayed_event.status == OrderStatus.PAID
