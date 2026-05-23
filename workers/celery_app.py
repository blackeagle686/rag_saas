"""
Celery application configuration.

Configures the Celery worker with Redis broker,
task auto-discovery, and retry settings.
"""

from __future__ import annotations

from celery import Celery

from api.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ragaas",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Retry settings
    task_acks_late=True,  # Acknowledge after task completes (not before)
    task_reject_on_worker_lost=True,  # Retry if worker crashes
    task_default_retry_delay=30,  # 30 seconds between retries
    task_max_retries=3,

    # Concurrency
    worker_prefetch_multiplier=1,  # Fair task distribution
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)

    # Result settings
    result_expires=3600,  # Results expire after 1 hour
)

# Auto-discover tasks in workers.tasks package
celery_app.autodiscover_tasks(["workers.tasks"])
