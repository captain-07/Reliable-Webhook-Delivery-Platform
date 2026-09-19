# app/workers/celery_app.py
import os
import sys

from celery import Celery

from app.core.config import settings

worker_pool = os.getenv("CELERY_WORKER_POOL") or (
    "solo" if sys.platform.startswith("win") else "prefork"
)

celery_app = Celery(
    "webhook_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    worker_pool=worker_pool,
)