"""Unit tests for Celery worker tasks."""

from apps.worker.tasks.health import ping


def test_celery_ping_task():
    result = ping()
    assert result["status"] == "ok"
    assert result["message"] == "pong"
    assert result["worker"] == "razorflow_worker"
