# app/workers/celery_app.py
from celery import Celery
from app.core.config import settings

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
)