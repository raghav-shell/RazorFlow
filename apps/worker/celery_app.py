"""Celery application configuration and task routing."""

from celery import Celery

from apps.api.config import get_settings

settings = get_settings()

celery_app = Celery(
    "razorflow_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "apps.worker.tasks.health",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Fair task distribution for reliable processing
    task_acks_late=True,  # Acknowledge tasks only after completion for zero-loss
    task_reject_on_worker_lost=True,
)
