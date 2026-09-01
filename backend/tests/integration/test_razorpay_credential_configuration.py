"""Tests proving that Razorpay credentials in demo and policy seeding originate from configuration and are never hardcoded."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from apps.api.config import Settings
from apps.api.routes.v1.demo import get_or_create_demo_merchant
from apps.api.routes.v1.policies import get_or_create_policy_config
from packages.adapters.razorpay.gateway_adapter import RazorpayGatewayAdapter
from packages.persistence.base import Base
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.ports.payment_gateway import GatewayProviderConfig


@pytest.fixture
async def in_memory_session():
    """Creates in-memory SQLite async engine and session for isolation."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_demo_merchant_seeding_uses_configured_settings(
    in_memory_session: AsyncSession, monkeypatch
):
    """Proves get_or_create_demo_merchant dynamically populates credentials from Settings."""
    custom_key_id = "rzp_test_custom_config_key_123"
    custom_key_secret = "custom_secret_456_configured"
    custom_webhook_secret = "custom_whsec_789_configured"

    # Patch get_settings to return custom configured values
    monkeypatch.setattr(
        "apps.api.routes.v1.demo.get_settings",
        lambda: Settings(
            RAZORPAY_KEY_ID=custom_key_id,
            RAZORPAY_KEY_SECRET=custom_key_secret,
            RAZORPAY_WEBHOOK_SECRET=custom_webhook_secret,
            RAZORPAY_MODE="test",
            RAZORPAY_PRODUCTION_ENABLED=False,
        ),
    )

    test_slug = f"test-merchant-{uuid.uuid4().hex[:6]}"
    merchant = await get_or_create_demo_merchant(in_memory_session, test_slug)
    await in_memory_session.commit()

    # Query the created provider config from the database
    stmt = select(MerchantProviderConfigModel).where(
        MerchantProviderConfigModel.merchant_id == merchant.id,
        MerchantProviderConfigModel.provider == "RAZORPAY",
    )
    prov_cfg = (await in_memory_session.execute(stmt)).scalar_one_or_none()

    assert prov_cfg is not None
    assert prov_cfg.key_id == custom_key_id
    assert prov_cfg.key_secret_enc == custom_key_secret
    assert prov_cfg.webhook_secret_enc == custom_webhook_secret
    assert prov_cfg.is_test_mode is True


@pytest.mark.asyncio
async def test_policy_config_seeding_uses_configured_settings(
    in_memory_session: AsyncSession, monkeypatch
):
    """Proves get_or_create_policy_config dynamically populates credentials from Settings."""
    custom_key_id = "rzp_test_policy_configured_key"
    custom_key_secret = "custom_policy_secret_configured"
    custom_webhook_secret = "custom_policy_whsec_configured"

    monkeypatch.setattr(
        "apps.api.routes.v1.policies.get_settings",
        lambda: Settings(
            RAZORPAY_KEY_ID=custom_key_id,
            RAZORPAY_KEY_SECRET=custom_key_secret,
            RAZORPAY_WEBHOOK_SECRET=custom_webhook_secret,
            RAZORPAY_MODE="test",
            RAZORPAY_PRODUCTION_ENABLED=False,
        ),
    )

    merchant = MerchantModel(
        name="Policy Configured Store",
        slug=f"policy-store-{uuid.uuid4().hex[:6]}",
        currency="INR",
        is_active=True,
    )
    in_memory_session.add(merchant)
    await in_memory_session.flush()

    prov_cfg, snapshot = await get_or_create_policy_config(in_memory_session, merchant)
    await in_memory_session.commit()

    assert prov_cfg.key_id == custom_key_id
    assert prov_cfg.key_secret_enc == custom_key_secret
    assert prov_cfg.webhook_secret_enc == custom_webhook_secret
    assert prov_cfg.is_test_mode is True


def test_production_guard_strictly_blocks_live_execution():
    """Confirms production credentials remain blocked when RAZORPAY_PRODUCTION_ENABLED=False."""
    adapter = RazorpayGatewayAdapter()

    prod_config = GatewayProviderConfig(
        key_id="rzp_live_production_key",
        key_secret="live_production_secret",
        webhook_secret="live_whsec",
        is_test_mode=False,
    )

    with pytest.raises(PermissionError) as exc_info:
        adapter._verify_safety_mode(prod_config)

    assert "CRITICAL SAFETY VIOLATION" in str(exc_info.value)
