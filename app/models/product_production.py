import uuid
from datetime import date, datetime
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ProductProduction(Base):
    __tablename__ = "product_productions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    produced_at = Column(Date, nullable=False, default=date.today)
    source = Column(String, nullable=False, default="production")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="productions")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_product_productions_quantity_positive"),
        Index("ix_product_productions_user_id", "user_id"),
        Index("ix_product_productions_product_id", "product_id"),
        Index("ix_product_productions_produced_at", "produced_at"),
    )
