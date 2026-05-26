import uuid
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class FairItem(Base):
    __tablename__ = "fair_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("sales_channels.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    planned_qty = Column(Integer, nullable=False)

    channel = relationship("SalesChannel")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("channel_id", "product_id", name="uq_fair_items_channel_product"),
        Index("ix_fair_items_channel_id", "channel_id"),
        Index("ix_fair_items_user_id", "user_id"),
    )
