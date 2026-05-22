import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)  # мягкие / деревянные / вязаные / прочее
    sale_price = Column(Numeric(10, 2), nullable=False)
    stock_qty = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    materials = relationship("ProductMaterial", back_populates="product", cascade="all, delete-orphan")
    sale_items = relationship("SaleItem", back_populates="product")

    __table_args__ = (
        Index("ix_products_user_id", "user_id"),
    )
