from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class ProductMaterialItemCreate(BaseModel):
    material_id: UUID
    quantity: Decimal


class ProductMaterialItemOut(BaseModel):
    id: UUID
    material_id: UUID
    product_id: UUID
    quantity: Decimal
    # Include material info
    material_name: Optional[str] = None
    material_unit: Optional[str] = None
    material_price: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sale_price: Decimal
    stock_qty: Optional[int] = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sale_price: Optional[Decimal] = None
    stock_qty: Optional[int] = None


class ProductOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sale_price: Decimal
    stock_qty: int
    cost_price: Optional[Decimal] = None  # Calculated field
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductDetailOut(ProductOut):
    photo: Optional[str] = None
    materials: Optional[List[ProductMaterialItemOut]] = []
