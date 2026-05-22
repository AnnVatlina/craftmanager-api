import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    contact = Column(String)  # телефон, Instagram, и т.д.
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sales = relationship("Sale", back_populates="buyer")

    __table_args__ = (
        Index("ix_buyers_user_id", "user_id"),
    )
