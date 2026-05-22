import uuid
from decimal import Decimal
from sqlalchemy import Column, Numeric, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    __table_args__ = (
        Index("ix_sale_items_user_id", "user_id"),
        Index("ix_sale_items_sale_id", "sale_id"),
        Index("ix_sale_items_product_id", "product_id"),
    )
