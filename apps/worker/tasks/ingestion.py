"""Celery background tasks for asynchronous raw webhook ingestion, case creation, and verification."""

import asyncio
import json
import uuid
from typing import Any, Dict, Optional

from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.api.config import get_settings
from apps.worker.celery_app import celery_app
from packages.adapters.razorpay.webhooks import parse_razorpay_webhook
from packages.orchestration.services.case_creation_service import CaseCreationService
from packages.orchestration.services.customer_enrichment_service import CustomerEnrichmentService
from packages.orchestration.services.order_payment_sync_service import OrderPaymentSyncService
from packages.orchestration.services.verification_service import VerificationService
from packages.persistence.database import get_sessionmaker
from packages.persistence.models.raw_event import RawWebhookEventModel

logger = get_task_logger(__name__)


async def _execute_ingestion_pipeline(
    session: AsyncSession,
    raw_event_id: uuid.UUID,
) -> Dict[str, Any]:
    """Internal business pipeline operating within an active database session."""
    # 1. Fetch raw event with lock
    raw_event = await session.get(RawWebhookEventModel, raw_event_id, with_for_update=True)
    if raw_event is None:
        logger.error(f"Raw webhook event '{raw_event_id}' not found in database.")
        return {"status": "error", "message": "Event not found"}

    if raw_event.processed:
        logger.info(f"Raw webhook event '{raw_event_id}' already processed. Skipping.")
        return {"status": "already_processed", "event_id": raw_event.event_id}

    merchant_id = raw_event.merchant_id

    # 2. Parse canonical payload
    try:
        raw_bytes = json.dumps(raw_event.payload).encode("utf-8")
        parsed_payload = parse_razorpay_webhook(raw_bytes, raw_event.headers)
    except Exception as e:
        logger.error(f"Failed to parse payload for raw event '{raw_event_id}': {e}")
        raw_event.processing_error = f"Parse Error: {e}"
        raw_event.processed = True
        return {"status": "error", "error": str(e)}

    # 3. Synchronize Customer, Order, and Payment
    customer = await OrderPaymentSyncService.sync_customer(
        session=session,
        merchant_id=merchant_id,
        payload=parsed_payload,
    )

    customer_id = customer.id if customer else None

    order = await OrderPaymentSyncService.sync_order(
        session=session,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payload=parsed_payload,
    )

    payment, is_new_payment = await OrderPaymentSyncService.sync_payment(
        session=session,
        merchant_id=merchant_id,
        order_id=order.id,
        customer_id=customer_id,
        payload=parsed_payload,
    )

    case_id = None

    # 4. Handle Payment Failure -> Case Creation & Enrichment
    if parsed_payload.event_type == "payment.failed" or parsed_payload.status == "failed":
        enrichment_context = await CustomerEnrichmentService.enrich_customer_context(
            session=session,
            merchant_id=merchant_id,
            customer_id=customer_id,
        )

        case, is_new_case = await CaseCreationService.create_or_update_recovery_case(
            session=session,
            merchant_id=merchant_id,
            order=order,
            payment=payment,
            customer=customer,
            payload=parsed_payload,
            enrichment_context=enrichment_context,
        )
        case_id = str(case.id)

    # 5. Handle Payment Capture -> Financial Verification & Recovery Confirmation
    elif (
        parsed_payload.event_type in ("payment.captured", "payment_link.paid", "order.paid")
        or parsed_payload.status == "captured"
    ):
        verif_result = await VerificationService.verify_from_webhook_event(
            session=session,
            event=parsed_payload,
            merchant_id=merchant_id,
        )
        if verif_result and verif_result.is_verified:
            case_id = str(verif_result.case_id)
            logger.info(f"Financial recovery confirmed for Case '{case_id}' via Webhook.")

    # 6. Mark raw event as processed
    raw_event.processed = True
    raw_event.processing_error = None
    await session.flush()

    logger.info(
        f"Successfully processed raw webhook '{raw_event.event_id}' (order={order.external_order_id}, case={case_id})."
    )
    return {
        "status": "success",
        "raw_event_id": str(raw_event.id),
        "order_id": str(order.id),
        "payment_id": str(payment.id),
        "case_id": case_id,
    }


async def _process_raw_webhook_async(
    raw_event_id_str: str,
    session: Optional[AsyncSession] = None,
    session_factory: Optional[async_sessionmaker] = None,
) -> Dict[str, Any]:
    """Async execution body for raw webhook processing."""
    raw_event_id = uuid.UUID(raw_event_id_str)

    if session is not None:
        return await _execute_ingestion_pipeline(session, raw_event_id)

    if session_factory is None:
        settings = get_settings()
        session_factory = get_sessionmaker(settings.DATABASE_URL)

    async with session_factory() as active_session:
        async with active_session.begin():
            return await _execute_ingestion_pipeline(active_session, raw_event_id)


@celery_app.task(
    name="tasks.ingestion.process_raw_webhook", bind=True, max_retries=3, default_retry_delay=5
)
def task_process_raw_webhook(self, raw_event_id: str) -> Dict[str, Any]:
    """
    Celery task orchestrating raw webhook ingestion, synchronization,
    RecoveryCase creation, and financial verification.
    """
    logger.info(f"Executing task_process_raw_webhook for raw_event_id={raw_event_id}")
    try:
        return asyncio.run(_process_raw_webhook_async(raw_event_id))
    except Exception as exc:
        logger.error(f"Task failed with error: {exc}. Retrying...")
        raise self.retry(exc=exc) from exc
