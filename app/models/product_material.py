import uuid
from decimal import Decimal
from sqlalchemy import Column, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ProductMaterial(Base):
    __tablename__ = "product_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(10, 4), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="materials")
    material = relationship("Material", back_populates="product_materials")

    __table_args__ = (
        Index("ix_product_materials_user_id", "user_id"),
        Index("ix_product_materials_product_id", "product_id"),
        Index("ix_product_materials_material_id", "material_id"),
        UniqueConstraint("product_id", "material_id", name="uq_product_material"),
    )
