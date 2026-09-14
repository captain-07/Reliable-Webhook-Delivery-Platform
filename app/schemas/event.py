# app/schemas/event.py
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EventCreate(BaseModel):
    event_type: str
    data: dict

class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    payload: dict
    idempotency_key: str | None
    created_at: datetime