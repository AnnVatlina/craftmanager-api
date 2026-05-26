from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class MaterialCreate(BaseModel):
    name: str
    unit: str
    price_per_unit: Decimal
    stock_qty: Optional[Decimal] = 0


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    price_per_unit: Optional[Decimal] = None
    stock_qty: Optional[Decimal] = None


class MaterialOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    unit: str
    price_per_unit: Decimal
    stock_qty: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class MaterialRestockRequest(BaseModel):
    qty: Decimal
    price_per_unit: Optional[Decimal] = None
    purchased_at: Optional[date] = None  # defaults to today server-side if omitted
