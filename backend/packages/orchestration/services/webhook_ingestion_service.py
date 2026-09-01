"""Service for validating, authenticating, and idempotently persisting raw gateway webhooks."""

import json
import logging
from typing import Any, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from packages.adapters.razorpay.webhooks import verify_razorpay_signature
from packages.persistence.models.merchant import MerchantModel, MerchantProviderConfigModel
from packages.persistence.models.raw_event import RawWebhookEventModel

logger = logging.getLogger(__name__)


class WebhookAuthenticationError(Exception):
    """Raised when webhook signature verification fails."""

    pass


class MerchantNotFoundError(Exception):
    """Raised when merchant cannot be resolved from slug."""

    pass


class ProviderConfigNotFoundError(Exception):
    """Raised when active provider credentials are not configured for merchant."""

    pass


class WebhookIngestionService:
    """
    Handles secure ingress of webhook payloads from external payment gateways.
    """

    @classmethod
    async def resolve_merchant_and_config(
        cls, session: AsyncSession, merchant_slug: str, provider: str = "RAZORPAY"
    ) -> Tuple[MerchantModel, MerchantProviderConfigModel]:
        """Resolves merchant and active provider configuration."""
        stmt = (
            select(MerchantModel)
            .options(selectinload(MerchantModel.provider_configs))
            .where(MerchantModel.slug == merchant_slug, MerchantModel.is_active.is_(True))
        )
        result = await session.execute(stmt)
        merchant = result.scalar_one_or_none()

        if merchant is None:
            raise MerchantNotFoundError(f"Active merchant with slug '{merchant_slug}' not found.")

        # Find active provider config
        config = next(
            (c for c in merchant.provider_configs if c.provider == provider and c.is_active),
            None,
        )
        if config is None:
            raise ProviderConfigNotFoundError(
                f"No active '{provider}' provider configuration found for merchant '{merchant_slug}'."
            )

        return merchant, config

    @classmethod
    async def ingest_razorpay_webhook(
        cls,
        session: AsyncSession,
        merchant_slug: str,
        raw_body_bytes: bytes,
        signature: str,
        headers: Dict[str, str],
    ) -> Tuple[bool, RawWebhookEventModel | None]:
        """
        Validates signature against raw body bytes, checks database idempotency,
        and durably persists the raw event record.

        Returns: (is_duplicate: bool, raw_event: RawWebhookEventModel | None)
        """
        merchant, config = await cls.resolve_merchant_and_config(session, merchant_slug, "RAZORPAY")

        # 1. Verify HMAC-SHA256 signature using constant-time comparison
        # Note: webhook_secret_enc holds secret (in production decrypted via envelope)
        webhook_secret = config.webhook_secret_enc
        is_valid = verify_razorpay_signature(raw_body_bytes, signature, webhook_secret)

        if not is_valid:
            logger.warning(
                f"Rejected webhook for merchant '{merchant_slug}': Invalid HMAC signature."
            )
            raise WebhookAuthenticationError("Invalid webhook signature.")

        # 2. Extract event metadata for idempotency
        try:
            payload_json: Dict[str, Any] = json.loads(raw_body_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Malformed JSON in webhook body for '{merchant_slug}': {e}")
            raise ValueError(f"Malformed JSON payload: {e}") from e

        event_type = payload_json.get("event", "unknown")
        event_id = (
            headers.get("x-razorpay-event-id")
            or headers.get("X-Razorpay-Event-Id")
            or payload_json.get("event_id")
        )

        if not event_id:
            # Deterministic fallback if header is omitted
            payment_id = (
                payload_json.get("payload", {})
                .get("payment", {})
                .get("entity", {})
                .get("id", "none")
            )
            created_at = payload_json.get("created_at", 0)
            event_id = f"evt_{payment_id}_{event_type}_{created_at}"

        # 3. Check for existing event in database (Fast path idempotency)
        stmt = select(RawWebhookEventModel).where(
            RawWebhookEventModel.merchant_id == merchant.id,
            RawWebhookEventModel.event_id == event_id,
        )
        existing_event = (await session.execute(stmt)).scalar_one_or_none()

        if existing_event is not None:
            logger.info(
                f"Deduplicated webhook '{event_id}' (type={event_type}) for merchant '{merchant_slug}'. Skipping."
            )
            return True, existing_event

        # 4. Insert new raw event record
        raw_event = RawWebhookEventModel(
            merchant_id=merchant.id,
            provider="RAZORPAY",
            event_id=event_id,
            event_type=event_type,
            payload=payload_json,
            signature=signature,
            headers={k: v for k, v in headers.items() if not k.lower().startswith("authorization")},
            processed=False,
        )

        try:
            session.add(raw_event)
            await session.flush()
            logger.info(
                f"Ingested raw webhook '{event_id}' (type={event_type}) for merchant '{merchant_slug}'."
            )
            return False, raw_event
        except IntegrityError:
            # Handle race condition where duplicate arrived concurrently
            await session.rollback()
            logger.info(
                f"Concurrent duplicate webhook '{event_id}' caught by unique constraint for merchant '{merchant_slug}'."
            )
            existing_event = (await session.execute(stmt)).scalar_one_or_none()
            return True, existing_event
