# app/schemas/subscription.py
import uuid
from pydantic import BaseModel, ConfigDict, HttpUrl

class SubscriptionCreate(BaseModel):
    target_url: HttpUrl
    secret: str
    event_types: list[str]

class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_url: HttpUrl
    event_types: list[str]
    is_active: bool