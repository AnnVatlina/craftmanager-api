import uuid
from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MaterialPurchase(Base):
    __tablename__ = "material_purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    purchased_at = Column(Date, nullable=False, default=date.today)
    quantity = Column(Numeric(10, 3), nullable=False)
    price_per_unit = Column(Numeric(10, 4), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)  # quantity * price_per_unit, stored for fast aggregation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    material = relationship("Material")

    __table_args__ = (
        Index("ix_material_purchases_user_id", "user_id"),
        Index("ix_material_purchases_purchased_at", "purchased_at"),
        Index("ix_material_purchases_material_id", "material_id"),
    )
