# app/models/delivery_attempt.py
import uuid, enum
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    DEAD = "dead"          # exhausted all retries

class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    attempt_number = Column(Integer, default=1)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    response_code = Column(Integer, nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())