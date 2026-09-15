# app/api/subscriptions.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    payload: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    sub = Subscription(**payload.model_dump(mode="json"))
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub