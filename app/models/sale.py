import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("buyers.id", ondelete="SET NULL"), nullable=True)
    sale_date = Column(Date, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    buyer = relationship("Buyer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sales_user_id", "user_id"),
        Index("ix_sales_buyer_id", "buyer_id"),
        Index("ix_sales_sale_date", "sale_date"),
    )
