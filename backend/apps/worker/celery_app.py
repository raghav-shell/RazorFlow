"""Celery application configuration and task routing."""

import ssl

from celery import Celery

from apps.api.config import get_settings

settings = get_settings()

is_ssl_broker = settings.CELERY_BROKER_URL.startswith("rediss://")
is_ssl_backend = settings.CELERY_RESULT_BACKEND.startswith("rediss://")

celery_app = Celery(
    "razorflow_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "apps.worker.tasks.health",
        "apps.worker.tasks.ingestion",
    ],
)

celery_config = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 300,  # 5 minutes max hard limit
    "task_soft_time_limit": 240,  # 4 minutes soft limit
    "worker_prefetch_multiplier": 1,  # Fair task distribution for reliable processing
    "task_acks_late": True,  # Acknowledge tasks only after completion for zero-loss
    "task_reject_on_worker_lost": True,
}

if is_ssl_broker:
    celery_config["broker_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_REQUIRED}

if is_ssl_backend:
    celery_config["redis_backend_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_REQUIRED}

celery_app.conf.update(**celery_config)
