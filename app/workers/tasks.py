# app/workers/tasks.py
from celery import shared_task
from sqlalchemy import select
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.event import Event
from app.models.subscription import Subscription

@celery_app.task(name="fan_out_event")
def fan_out_event(event_id: str):
    """Looks up matching subscriptions and spawns one delivery task per subscriber."""
    with SessionLocal() as db:
        event = db.get(Event, event_id)
        subs = db.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.event_types.contains([event.event_type]),
            )
        ).scalars().all()

        for sub in subs:
            deliver_webhook.delay(event_id=str(event.id), subscription_id=str(sub.id))