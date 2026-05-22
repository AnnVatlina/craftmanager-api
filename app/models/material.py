import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)  # г / м / шт / мл
    price_per_unit = Column(Numeric(10, 4), nullable=False)
    stock_qty = Column(Numeric(10, 3), default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    product_materials = relationship("ProductMaterial", back_populates="material")

    __table_args__ = (
        Index("ix_materials_user_id", "user_id"),
    )
