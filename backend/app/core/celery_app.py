"""Celery application instance for async task processing."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ap_ops_manager",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks from app.tasks package (when created)
celery_app.autodiscover_tasks(["app.tasks"], force=True)
