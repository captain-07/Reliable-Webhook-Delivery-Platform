# app/api/deliveries.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.delivery_attempt import DeliveryAttempt
from app.schemas.delivery import EventDeliveriesResponse

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.get("/events/{event_id}/deliveries", response_model=EventDeliveriesResponse)
async def get_event_deliveries(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeliveryAttempt)
        .where(DeliveryAttempt.event_id == event_id)
        .order_by(DeliveryAttempt.attempted_at)
    )
    attempts = result.scalars().all()
    if not attempts:
        raise HTTPException(status_code=404, detail="No delivery attempts found for this event")
    return EventDeliveriesResponse(event_id=event_id, attempts=attempts)