"""Concrete Razorpay Payment Gateway Adapter implementing PaymentGatewayPort."""

import asyncio
import logging
from typing import Any, Dict, Literal, Optional

import httpx

from apps.api.config import get_settings
from packages.ports.payment_gateway import (
    GatewayNotificationResult,
    GatewayOrderVerificationResult,
    GatewayPaymentLinkResult,
    GatewayPaymentVerificationResult,
    GatewayProviderConfig,
    PaymentGatewayPort,
)

logger = logging.getLogger(__name__)


def is_retryable_http_status(status_code: int) -> bool:
    """Returns True if status code represents a transient gateway failure."""
    return status_code in (408, 429, 500, 502, 503, 504)


class RazorpayGatewayAdapter(PaymentGatewayPort):
    """
    Official Razorpay API Adapter with test-mode safety, explicit timeouts, and retry policies.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        connect_timeout: float = 3.0,
        read_timeout: float = 8.0,
        max_retries: int = 2,
    ) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.RAZORPAY_BASE_URL).rstrip("/")
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries

    def _verify_safety_mode(self, config: GatewayProviderConfig) -> None:
        settings = get_settings()
        if not config.is_test_mode and not settings.RAZORPAY_PRODUCTION_ENABLED:
            raise PermissionError(
                "CRITICAL SAFETY VIOLATION: Production Razorpay credentials supplied but "
                "RAZORPAY_PRODUCTION_ENABLED is False. Execution blocked."
            )

    async def _execute_request(
        self,
        config: GatewayProviderConfig,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        is_idempotent_operation: bool = False,
    ) -> httpx.Response:
        self._verify_safety_mode(config)
        url = f"{self.base_url}{path}"
        req_headers = {"User-Agent": "RazorFlow-Recovery/1.0", **(headers or {})}

        auth = (config.key_id, config.key_secret)
        timeout = httpx.Timeout(self.read_timeout, connect=self.connect_timeout)

        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=json_data,
                        headers=req_headers,
                        auth=auth,
                    )

                    # Return immediately on success or client 4xx (except 429 rate limit)
                    if response.status_code < 400 or response.status_code in (400, 401, 403, 404):
                        return response

                    # If server error / 429 and operation is safe/idempotent to retry
                    if is_retryable_http_status(response.status_code) and (
                        is_idempotent_operation or method == "GET"
                    ):
                        if attempt < self.max_retries:
                            backoff_seconds = 0.5 * (2**attempt)
                            logger.warning(
                                f"Razorpay API {method} {path} returned HTTP {response.status_code}. "
                                f"Retrying in {backoff_seconds}s (Attempt {attempt + 1}/{self.max_retries})."
                            )
                            await asyncio.sleep(backoff_seconds)
                            continue

                    return response

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
                last_exception = exc
                if attempt < self.max_retries and (is_idempotent_operation or method == "GET"):
                    backoff_seconds = 0.5 * (2**attempt)
                    logger.warning(
                        f"Razorpay network error on {method} {path}: {exc}. "
                        f"Retrying in {backoff_seconds}s (Attempt {attempt + 1}/{self.max_retries})."
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    break

        if last_exception:
            raise last_exception
        raise httpx.RequestError(f"Request failed after {self.max_retries} attempts.")

    async def create_payment_link(
        self,
        config: GatewayProviderConfig,
        order_id: str,
        amount_cents: int,
        currency: str,
        customer_contact: Optional[str],
        customer_email: Optional[str],
        customer_name: Optional[str],
        description: str,
        expire_by_timestamp: int,
        idempotency_key: str,
        reference_id: Optional[str] = None,
    ) -> GatewayPaymentLinkResult:
        payload: Dict[str, Any] = {
            "amount": amount_cents,
            "currency": currency,
            "description": description,
            "expire_by": expire_by_timestamp,
            "reference_id": reference_id or idempotency_key,
            "customer": {
                "name": customer_name or "Valued Customer",
                "contact": customer_contact,
                "email": customer_email,
            },
            "notify": {"sms": bool(customer_contact), "email": bool(customer_email)},
            "reminder_enable": True,
            "notes": {"order_id": order_id, "idempotency_key": idempotency_key},
        }

        # Filter None customer keys
        payload["customer"] = {k: v for k, v in payload["customer"].items() if v is not None}

        headers = {"X-Razorpay-Idempotency-Key": idempotency_key}

        try:
            resp = await self._execute_request(
                config=config,
                method="POST",
                path="/payment_links",
                json_data=payload,
                headers=headers,
                is_idempotent_operation=True,
            )

            body = resp.json() if resp.text else {}

            if resp.status_code in (200, 201):
                return GatewayPaymentLinkResult(
                    is_success=True,
                    gateway_link_id=body.get("id"),
                    short_url=body.get("short_url"),
                    status=body.get("status", "created"),
                    amount_cents=body.get("amount", amount_cents),
                    currency=body.get("currency", currency),
                    raw_response=body,
                )

            err_info = body.get("error", {})
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code=err_info.get("code", str(resp.status_code)),
                error_message=err_info.get("description", resp.text),
                raw_response=body,
                is_retryable=is_retryable_http_status(resp.status_code),
            )

        except Exception as e:
            logger.error(f"Razorpay create_payment_link failed: {e}")
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code="CONNECTION_ERROR",
                error_message=str(e),
                is_retryable=True,
            )

    async def send_payment_link_reminder(
        self,
        config: GatewayProviderConfig,
        gateway_link_id: str,
        medium: Literal["sms", "email"],
    ) -> GatewayNotificationResult:
        try:
            resp = await self._execute_request(
                config=config,
                method="POST",
                path=f"/payment_links/{gateway_link_id}/notify_by/{medium}",
                is_idempotent_operation=False,  # Notification is not strictly idempotent
            )

            body = resp.json() if resp.text else {}

            if resp.status_code in (200, 201):
                return GatewayNotificationResult(
                    is_success=True,
                    status="sent",
                    raw_response=body,
                )

            err_info = body.get("error", {})
            return GatewayNotificationResult(
                is_success=False,
                error_code=err_info.get("code", str(resp.status_code)),
                error_message=err_info.get("description", resp.text),
                raw_response=body,
                is_retryable=is_retryable_http_status(resp.status_code),
            )

        except Exception as e:
            logger.error(f"Razorpay send_payment_link_reminder failed: {e}")
            return GatewayNotificationResult(
                is_success=False,
                error_code="CONNECTION_ERROR",
                error_message=str(e),
                is_retryable=True,
            )

    async def fetch_payment_link_status(
        self,
        config: GatewayProviderConfig,
        gateway_link_id: str,
    ) -> GatewayPaymentLinkResult:
        try:
            resp = await self._execute_request(
                config=config,
                method="GET",
                path=f"/payment_links/{gateway_link_id}",
                is_idempotent_operation=True,
            )

            body = resp.json() if resp.text else {}

            if resp.status_code == 200:
                return GatewayPaymentLinkResult(
                    is_success=True,
                    gateway_link_id=body.get("id"),
                    short_url=body.get("short_url"),
                    status=body.get("status", "created"),
                    amount_cents=body.get("amount"),
                    currency=body.get("currency"),
                    raw_response=body,
                )

            err_info = body.get("error", {})
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code=err_info.get("code", str(resp.status_code)),
                error_message=err_info.get("description", resp.text),
                raw_response=body,
            )

        except Exception as e:
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code="CONNECTION_ERROR",
                error_message=str(e),
                is_retryable=True,
            )

    async def fetch_payment_status(
        self,
        config: GatewayProviderConfig,
        gateway_payment_id: str,
    ) -> GatewayPaymentVerificationResult:
        try:
            resp = await self._execute_request(
                config=config,
                method="GET",
                path=f"/payments/{gateway_payment_id}",
                is_idempotent_operation=True,
            )

            body = resp.json() if resp.text else {}

            if resp.status_code == 200:
                return GatewayPaymentVerificationResult(
                    is_success=True,
                    payment_id=body.get("id", gateway_payment_id),
                    status=body.get("status", "unknown"),
                    amount_cents=body.get("amount", 0),
                    currency=body.get("currency", "INR"),
                    method=body.get("method"),
                    order_id=body.get("order_id"),
                    raw_response=body,
                )

            err_info = body.get("error", {})
            return GatewayPaymentVerificationResult(
                is_success=False,
                payment_id=gateway_payment_id,
                status="error",
                amount_cents=0,
                currency="INR",
                error_code=err_info.get("code", str(resp.status_code)),
                error_description=err_info.get("description", resp.text),
                raw_response=body,
            )

        except Exception as e:
            return GatewayPaymentVerificationResult(
                is_success=False,
                payment_id=gateway_payment_id,
                status="error",
                amount_cents=0,
                currency="INR",
                error_code="CONNECTION_ERROR",
                error_description=str(e),
                is_retryable=True,
            )

    async def fetch_order_status(
        self,
        config: GatewayProviderConfig,
        gateway_order_id: str,
    ) -> GatewayOrderVerificationResult:
        try:
            resp = await self._execute_request(
                config=config,
                method="GET",
                path=f"/orders/{gateway_order_id}",
                is_idempotent_operation=True,
            )

            body = resp.json() if resp.text else {}

            if resp.status_code == 200:
                return GatewayOrderVerificationResult(
                    is_success=True,
                    order_id=body.get("id", gateway_order_id),
                    status=body.get("status", "unknown"),
                    amount_cents=body.get("amount", 0),
                    amount_paid_cents=body.get("amount_paid", 0),
                    currency=body.get("currency", "INR"),
                    raw_response=body,
                )

            err_info = body.get("error", {})
            return GatewayOrderVerificationResult(
                is_success=False,
                order_id=gateway_order_id,
                status="error",
                amount_cents=0,
                amount_paid_cents=0,
                currency="INR",
                error_code=err_info.get("code", str(resp.status_code)),
                error_message=err_info.get("description", resp.text),
                raw_response=body,
            )

        except Exception as e:
            return GatewayOrderVerificationResult(
                is_success=False,
                order_id=gateway_order_id,
                status="error",
                amount_cents=0,
                amount_paid_cents=0,
                currency="INR",
                error_code="CONNECTION_ERROR",
                error_message=str(e),
                is_retryable=True,
            )
