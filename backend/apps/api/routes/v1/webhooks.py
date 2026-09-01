"""Razorpay Webhook Ingestion API route."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_db_session
from apps.worker.tasks.ingestion import task_process_raw_webhook
from packages.orchestration.services.webhook_ingestion_service import (
    MerchantNotFoundError,
    ProviderConfigNotFoundError,
    WebhookAuthenticationError,
    WebhookIngestionService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay/{merchant_slug}", summary="Ingest Razorpay Webhook Event")
async def ingest_razorpay_webhook_endpoint(
    merchant_slug: str,
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Receives raw Razorpay webhook payload, verifies HMAC-SHA256 signature against
    the exact request bytes, checks database idempotency, and queues asynchronous processing.
    """
    # 1. Read exact raw request body bytes for signature validation
    raw_body_bytes = await request.body()

    # Extract headers
    headers_dict = dict(request.headers)

    try:
        is_duplicate, raw_event = await WebhookIngestionService.ingest_razorpay_webhook(
            session=db,
            merchant_slug=merchant_slug,
            raw_body_bytes=raw_body_bytes,
            signature=x_razorpay_signature,
            headers=headers_dict,
        )
    except WebhookAuthenticationError as e:
        logger.warning(f"Webhook authentication failed for merchant '{merchant_slug}': {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        ) from e
    except (MerchantNotFoundError, ProviderConfigNotFoundError) as e:
        logger.warning(f"Merchant or provider not found for slug '{merchant_slug}': {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValueError as e:
        logger.error(f"Malformed webhook payload for merchant '{merchant_slug}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # 2. Handle Duplicate Webhooks Idempotently
    if is_duplicate or raw_event is None:
        return {
            "status": "duplicate_ignored",
            "message": "Webhook event was already received and processed.",
            "event_id": raw_event.event_id if raw_event else "unknown",
        }

    # 3. Commit the database transaction before queueing background Celery task
    await db.commit()

    # 4. Dispatch Asynchronous Celery Processing Task
    try:
        task_process_raw_webhook.delay(str(raw_event.id))
    except Exception as e:
        # If Celery broker is offline in synchronous/dev mode, task remains persisted in DB
        logger.warning(
            f"Failed to enqueue Celery task immediately (will be picked up by worker): {e}"
        )

    return {
        "status": "accepted",
        "event_id": raw_event.event_id,
        "event_type": raw_event.event_type,
        "raw_event_id": str(raw_event.id),
    }
