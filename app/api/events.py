# app/api/events.py
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse
from app.workers.tasks import fan_out_event
from app.core.rate_limit import limiter

from app.core.security import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/events", response_model=EventResponse, status_code=202)
@limiter.limit("100/minute")
async def ingest_event(
    request: Request,
    payload: EventCreate,
    idempotency_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    if idempotency_key:
        existing = await db.scalar(
            select(Event).where(Event.idempotency_key == idempotency_key)
        )
        if existing:
            return existing  # return original, don't reprocess

    event = Event(
        event_type=payload.event_type,
        payload=payload.data,
        idempotency_key=idempotency_key,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    fan_out_event.delay(str(event.id))   # hand off to Celery, don't block
    return event