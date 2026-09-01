"""Abstract Port for Payment Gateway operations (Hexagonal Architecture)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional


@dataclass(frozen=True)
class GatewayProviderConfig:
    key_id: str
    key_secret: str
    webhook_secret: str
    is_test_mode: bool = True
    additional_config: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GatewayPaymentLinkResult:
    is_success: bool
    gateway_link_id: Optional[str] = None
    short_url: Optional[str] = None
    status: str = "created"  # created, paid, expired, cancelled
    amount_cents: Optional[int] = None
    currency: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_retryable: bool = False


@dataclass(frozen=True)
class GatewayNotificationResult:
    is_success: bool
    status: str = "sent"
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_retryable: bool = False


@dataclass(frozen=True)
class GatewayPaymentVerificationResult:
    is_success: bool
    payment_id: str
    status: str  # captured, authorized, failed, refunded
    amount_cents: int
    currency: str
    method: Optional[str] = None
    order_id: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    is_retryable: bool = False


@dataclass(frozen=True)
class GatewayOrderVerificationResult:
    is_success: bool
    order_id: str
    status: str  # created, attempted, paid
    amount_cents: int
    amount_paid_cents: int
    currency: str
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_retryable: bool = False


class PaymentGatewayPort(ABC):
    """
    Abstract Payment Gateway Interface.
    Decouples domain and application logic from specific Razorpay SDK/HTTP details.
    """

    @abstractmethod
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
        """Generates an idempotent hosted payment link."""
        pass

    @abstractmethod
    async def send_payment_link_reminder(
        self,
        config: GatewayProviderConfig,
        gateway_link_id: str,
        medium: Literal["sms", "email"],
    ) -> GatewayNotificationResult:
        """Triggers an official customer notification/reminder for a payment link."""
        pass

    @abstractmethod
    async def fetch_payment_link_status(
        self,
        config: GatewayProviderConfig,
        gateway_link_id: str,
    ) -> GatewayPaymentLinkResult:
        """Fetches current status of a payment link from gateway."""
        pass

    @abstractmethod
    async def fetch_payment_status(
        self,
        config: GatewayProviderConfig,
        gateway_payment_id: str,
    ) -> GatewayPaymentVerificationResult:
        """Fetches confirmed status of a payment from gateway."""
        pass

    @abstractmethod
    async def fetch_order_status(
        self,
        config: GatewayProviderConfig,
        gateway_order_id: str,
    ) -> GatewayOrderVerificationResult:
        """Fetches confirmed status of an order from gateway."""
        pass
