# app/schemas/delivery.py
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.delivery_attempt import DeliveryStatus

class DeliveryAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    attempt_number: int
    status: DeliveryStatus
    response_code: int | None
    attempted_at: datetime

class EventDeliveriesResponse(BaseModel):
    event_id: uuid.UUID
    attempts: list[DeliveryAttemptResponse]