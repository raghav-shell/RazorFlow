"""Integration tests for POST /api/v1/webhooks/razorpay/{merchant_slug} endpoint."""

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel


def generate_rzp_signature(body_bytes: bytes, secret: str) -> str:
    """Helper to compute valid HMAC-SHA256 signature."""
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_webhook_ingestion_success(async_client: AsyncClient, async_db_session: AsyncSession):
    # 1. Create Merchant and Razorpay config
    merchant = MerchantModel(name="Tech Store", slug="tech-store", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    config = MerchantProviderConfigModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        key_id="rzp_key_test",
        key_secret_enc="secret",
        webhook_secret_enc="whsec_test_secret_123",
        is_active=True,
    )
    async_db_session.add(config)
    await async_db_session.commit()

    # 2. Build Webhook Payload
    payload = {
        "entity": "event",
        "account_id": "acc_001",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_100",
                    "order_id": "order_test_100",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "failed",
                    "email": "user@example.com",
                    "contact": "+919999988888",
                    "error_code": "BAD_REQUEST_PAYMENT_TIMED_OUT",
                    "error_description": "Bank timeout",
                }
            }
        },
        "created_at": 1700000000,
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    signature = generate_rzp_signature(body_bytes, "whsec_test_secret_123")

    headers = {
        "X-Razorpay-Signature": signature,
        "X-Razorpay-Event-Id": "evt_unique_100",
        "Content-Type": "application/json",
    }

    # 3. Dispatch Webhook Request
    response = await async_client.post(
        "/api/v1/webhooks/razorpay/tech-store",
        content=body_bytes,
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event_id"] == "evt_unique_100"


@pytest.mark.asyncio
async def test_webhook_ingestion_duplicate_idempotency(
    async_client: AsyncClient, async_db_session: AsyncSession
):
    merchant = MerchantModel(name="Book Store", slug="book-store", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    config = MerchantProviderConfigModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        key_id="rzp_key_test",
        key_secret_enc="secret",
        webhook_secret_enc="whsec_secret_books",
        is_active=True,
    )
    async_db_session.add(config)
    await async_db_session.commit()

    payload = {
        "entity": "event",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_200",
                    "order_id": "order_test_200",
                    "amount": 50000,
                    "currency": "INR",
                    "status": "failed",
                }
            }
        },
        "created_at": 1700000000,
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    signature = generate_rzp_signature(body_bytes, "whsec_secret_books")
    headers = {"X-Razorpay-Signature": signature, "X-Razorpay-Event-Id": "evt_duplicate_test"}

    # First delivery -> Accepted
    res1 = await async_client.post(
        "/api/v1/webhooks/razorpay/book-store", content=body_bytes, headers=headers
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "accepted"

    # Second delivery with exact same event ID -> Duplicate Ignored (HTTP 200)
    res2 = await async_client.post(
        "/api/v1/webhooks/razorpay/book-store", content=body_bytes, headers=headers
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_webhook_ingestion_invalid_signature(
    async_client: AsyncClient, async_db_session: AsyncSession
):
    merchant = MerchantModel(name="Shoe Store", slug="shoe-store", currency="INR")
    async_db_session.add(merchant)
    await async_db_session.flush()

    config = MerchantProviderConfigModel(
        merchant_id=merchant.id,
        provider="RAZORPAY",
        key_id="rzp_key",
        key_secret_enc="sec",
        webhook_secret_enc="whsec_shoe",
        is_active=True,
    )
    async_db_session.add(config)
    await async_db_session.commit()

    response = await async_client.post(
        "/api/v1/webhooks/razorpay/shoe-store",
        content=b'{"event":"payment.failed"}',
        headers={"X-Razorpay-Signature": "bad_signature_hex_123"},
    )
    assert response.status_code == 401
    assert "Invalid webhook signature" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_ingestion_unknown_merchant(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/webhooks/razorpay/non-existent-merchant",
        content=b'{"event":"payment.failed"}',
        headers={"X-Razorpay-Signature": "dummy"},
    )
    assert response.status_code == 404
