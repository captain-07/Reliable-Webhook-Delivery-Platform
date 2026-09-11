# app/models/subscription.py
import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_url = Column(String, nullable=False)
    secret = Column(String, nullable=False)          # used for HMAC signing
    event_types = Column(ARRAY(String), nullable=False)  # e.g. ["order.created"]
    is_active = Column(Boolean, default=True)