"""Celery worker healthcheck and heartbeat task."""

from celery.utils.log import get_task_logger

from apps.worker.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="tasks.health.ping")
def ping() -> dict:
    """Worker heartbeat test task returning pong."""
    logger.info("Executing Celery health check ping.")
    return {"status": "ok", "message": "pong", "worker": "razorflow_worker"}
