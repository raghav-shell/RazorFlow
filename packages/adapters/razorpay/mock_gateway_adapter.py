"""Mock Payment Gateway Adapter for deterministic testing, demo simulation, and failure injection."""

import asyncio
import uuid
from typing import Dict, Literal, Optional

from packages.ports.payment_gateway import (
    GatewayNotificationResult,
    GatewayOrderVerificationResult,
    GatewayPaymentLinkResult,
    GatewayPaymentVerificationResult,
    GatewayProviderConfig,
    PaymentGatewayPort,
)


class MockPaymentGatewayAdapter(PaymentGatewayPort):
    """
    In-memory Mock Payment Gateway with configurable failure injection and recorded history.
    """

    def __init__(
        self,
        should_timeout: bool = False,
        should_fail_500: bool = False,
        should_fail_429: bool = False,
        custom_error_message: Optional[str] = None,
        force_payment_status: str = "captured",
        force_link_status: str = "created",
    ) -> None:
        self.should_timeout = should_timeout
        self.should_fail_500 = should_fail_500
        self.should_fail_429 = should_fail_429
        self.custom_error_message = custom_error_message
        self.force_payment_status = force_payment_status
        self.force_link_status = force_link_status

        # In-memory stores
        self.created_links: Dict[str, dict] = {}
        self.sent_notifications: list[dict] = []
        self.idempotency_keys_seen: set[str] = set()

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
        if self.should_timeout:
            await asyncio.sleep(0.05)
            raise TimeoutError("Mock gateway timeout on create_payment_link")

        if self.should_fail_500:
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code="GATEWAY_INTERNAL_ERROR",
                error_message=self.custom_error_message or "Internal Server Error",
                is_retryable=True,
            )

        if self.should_fail_429:
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code="RATE_LIMIT_EXCEEDED",
                error_message="Too Many Requests",
                is_retryable=True,
            )

        # Handle duplicate idempotency key (mock gateway recognizes same request)
        if idempotency_key in self.idempotency_keys_seen:
            existing = self.created_links.get(idempotency_key)
            if existing:
                return GatewayPaymentLinkResult(
                    is_success=True,
                    gateway_link_id=existing["id"],
                    short_url=existing["short_url"],
                    status=existing["status"],
                    amount_cents=existing["amount"],
                    currency=existing["currency"],
                    raw_response=existing,
                )

        link_id = f"plink_{uuid.uuid4().hex[:14]}"
        short_url = f"https://rzp.io/i/{uuid.uuid4().hex[:8]}"

        link_record = {
            "id": link_id,
            "short_url": short_url,
            "status": self.force_link_status,
            "amount": amount_cents,
            "currency": currency,
            "order_id": order_id,
            "reference_id": reference_id,
            "idempotency_key": idempotency_key,
        }

        self.created_links[idempotency_key] = link_record
        self.created_links[link_id] = link_record
        self.idempotency_keys_seen.add(idempotency_key)

        return GatewayPaymentLinkResult(
            is_success=True,
            gateway_link_id=link_id,
            short_url=short_url,
            status=self.force_link_status,
            amount_cents=amount_cents,
            currency=currency,
            raw_response=link_record,
        )

    async def send_payment_link_reminder(
        self,
        config: GatewayProviderConfig,
        gateway_link_id: str,
        medium: Literal["sms", "email"],
    ) -> GatewayNotificationResult:
        if self.should_timeout:
            await asyncio.sleep(0.05)
            raise TimeoutError("Mock gateway timeout on send_payment_link_reminder")

        if self.should_fail_500:
            return GatewayNotificationResult(
                is_success=False,
                error_code="GATEWAY_INTERNAL_ERROR",
                error_message="Internal Server Error",
                is_retryable=True,
            )

        notif_record = {
            "gateway_link_id": gateway_link_id,
            "medium": medium,
            "status": "sent",
        }
        self.sent_notifications.append(notif_record)

        return GatewayNotificationResult(
            is_success=True,
            status="sent",
            raw_response=notif_record,
        )

    async def fetch_payment_link_status(
        self,
        config: GatewayProviderConfig,
        gateway_link_id: str,
    ) -> GatewayPaymentLinkResult:
        if self.should_timeout:
            await asyncio.sleep(0.05)
            raise TimeoutError("Mock gateway timeout on fetch_payment_link_status")

        link = self.created_links.get(gateway_link_id)
        if not link:
            return GatewayPaymentLinkResult(
                is_success=False,
                error_code="BAD_REQUEST_ERROR",
                error_message="Payment Link not found",
            )

        return GatewayPaymentLinkResult(
            is_success=True,
            gateway_link_id=link["id"],
            short_url=link["short_url"],
            status=self.force_link_status,
            amount_cents=link["amount"],
            currency=link["currency"],
            raw_response=link,
        )

    async def fetch_payment_status(
        self,
        config: GatewayProviderConfig,
        gateway_payment_id: str,
    ) -> GatewayPaymentVerificationResult:
        if self.should_timeout:
            await asyncio.sleep(0.05)
            raise TimeoutError("Mock gateway timeout on fetch_payment_status")

        if self.should_fail_500:
            return GatewayPaymentVerificationResult(
                is_success=False,
                payment_id=gateway_payment_id,
                status="error",
                amount_cents=0,
                currency="INR",
                error_code="SERVER_ERROR",
                error_description="Internal Server Error",
                is_retryable=True,
            )

        return GatewayPaymentVerificationResult(
            is_success=True,
            payment_id=gateway_payment_id,
            status=self.force_payment_status,
            amount_cents=250000,
            currency="INR",
            method="upi",
            raw_response={"id": gateway_payment_id, "status": self.force_payment_status},
        )

    async def fetch_order_status(
        self,
        config: GatewayProviderConfig,
        gateway_order_id: str,
    ) -> GatewayOrderVerificationResult:
        return GatewayOrderVerificationResult(
            is_success=True,
            order_id=gateway_order_id,
            status="paid" if self.force_payment_status == "captured" else "attempted",
            amount_cents=250000,
            amount_paid_cents=250000 if self.force_payment_status == "captured" else 0,
            currency="INR",
            raw_response={"id": gateway_order_id, "status": "paid"},
        )
