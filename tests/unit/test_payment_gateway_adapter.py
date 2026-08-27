"""Unit tests for Razorpay Payment Gateway Adapter and test-mode safety."""

import pytest

from apps.api.config import get_settings
from packages.adapters.razorpay.gateway_adapter import (
    RazorpayGatewayAdapter,
    is_retryable_http_status,
)
from packages.ports.payment_gateway import GatewayProviderConfig


def test_retryable_http_status_classification():
    assert is_retryable_http_status(500) is True
    assert is_retryable_http_status(502) is True
    assert is_retryable_http_status(503) is True
    assert is_retryable_http_status(504) is True
    assert is_retryable_http_status(429) is True
    assert is_retryable_http_status(408) is True
    # Non-retryable
    assert is_retryable_http_status(400) is False
    assert is_retryable_http_status(401) is False
    assert is_retryable_http_status(403) is False
    assert is_retryable_http_status(404) is False
    assert is_retryable_http_status(200) is False


def test_production_mode_safety_guard():
    adapter = RazorpayGatewayAdapter()
    settings = get_settings()
    # Ensure production is disabled in test settings
    assert settings.RAZORPAY_PRODUCTION_ENABLED is False

    # Providing production credentials with is_test_mode=False must raise PermissionError
    prod_config = GatewayProviderConfig(
        key_id="rzp_live_123456",
        key_secret="live_secret_abc",
        webhook_secret="live_whsec",
        is_test_mode=False,
    )

    with pytest.raises(PermissionError) as exc_info:
        adapter._verify_safety_mode(prod_config)
    assert "CRITICAL SAFETY VIOLATION" in str(exc_info.value)


def test_test_mode_credentials_allowed():
    adapter = RazorpayGatewayAdapter()
    test_config = GatewayProviderConfig(
        key_id="rzp_test_123456",
        key_secret="test_secret_abc",
        webhook_secret="test_whsec",
        is_test_mode=True,
    )
    # Must not raise
    adapter._verify_safety_mode(test_config)
