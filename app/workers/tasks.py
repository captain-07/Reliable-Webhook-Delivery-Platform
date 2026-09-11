# app/workers/tasks.py

import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.delivery_attempt import DeliveryAttempt, DeliveryStatus
from app.models.event import Event
from app.models.subscription import Subscription
from app.services.delivery import send_webhook
from app.workers.celery_app import celery_app


MAX_ATTEMPTS = 5


# ─────────────────────────────────────────────
# Fan-out task
# ─────────────────────────────────────────────

@celery_app.task(name="fan_out_event")
def fan_out_event(event_id: str):
    """
    Find all matching active subscriptions
    and create one delivery task per subscriber.
    """

    with SessionLocal() as db:

        # Find the event
        event = db.get(Event, event_id)

        # Find active subscriptions interested in this event type
        subs = db.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.event_types.contains(
                    [event.event_type]
                ),
            )
        ).scalars().all()

        # Create one independent delivery task per subscriber
        for sub in subs:
            deliver_webhook.delay(
                event_id=str(event.id),
                subscription_id=str(sub.id),
            )


# ─────────────────────────────────────────────
# Webhook delivery task
# ─────────────────────────────────────────────

@celery_app.task(
    name="deliver_webhook",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,          # 1s → 2s → 4s → 8s...
    retry_backoff_max=3600,      # Maximum 1 hour
    retry_jitter=True,           # Randomize retry timing
    max_retries=MAX_ATTEMPTS,
)
def deliver_webhook(
    self,
    event_id: str,
    subscription_id: str,
):
    """
    Send an event to one subscriber.
    Failed deliveries are retried with exponential backoff.
    """

    with SessionLocal() as db:

        # Get event and subscriber
        event = db.get(Event, event_id)
        sub = db.get(Subscription, subscription_id)

        # Celery starts retries from 0
        # So retry count + 1 = actual attempt number
        attempt_number = self.request.retries + 1

        try:
            # Send the webhook
            response = asyncio.run(
                send_webhook(
                    sub.target_url,
                    event.payload,
                    sub.secret,
                )
            )

            # Raise an exception for HTTP 4xx/5xx
            response.raise_for_status()

            status = DeliveryStatus.SUCCESS
            code = response.status_code

        except Exception as exc:

            # Get HTTP status code if available
            code = getattr(
                getattr(exc, "response", None),
                "status_code",
                None,
            )

            # Mark as DEAD if maximum attempts reached
            status = (
                DeliveryStatus.DEAD
                if attempt_number >= MAX_ATTEMPTS
                else DeliveryStatus.FAILED
            )

            # Save failed attempt
            db.add(
                DeliveryAttempt(
                    event_id=event.id,
                    subscription_id=sub.id,
                    attempt_number=attempt_number,
                    status=status,
                    response_code=code,
                )
            )

            db.commit()

            # Tell Celery to retry
            raise self.retry(exc=exc)

        # Save successful attempt
        db.add(
            DeliveryAttempt(
                event_id=event.id,
                subscription_id=sub.id,
                attempt_number=attempt_number,
                status=status,
                response_code=code,
            )
        )

        db.commit()