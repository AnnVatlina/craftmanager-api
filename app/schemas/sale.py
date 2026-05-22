from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class SaleItemCreate(BaseModel):
    product_id: Optional[UUID] = None
    quantity: int
    price: Decimal


class SaleItemOut(BaseModel):
    id: UUID
    sale_id: UUID
    product_id: Optional[UUID] = None
    quantity: int
    price: Decimal
    product_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SaleCreate(BaseModel):
    channel_id: Optional[UUID] = None
    sale_date: date
    notes: Optional[str] = None
    items: List[SaleItemCreate]


class SaleUpdate(BaseModel):
    channel_id: Optional[UUID] = None
    sale_date: Optional[date] = None
    notes: Optional[str] = None


class SaleOut(BaseModel):
    id: UUID
    user_id: UUID
    channel_id: Optional[UUID] = None
    sale_date: date
    notes: Optional[str] = None
    total_amount: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleDetailOut(SaleOut):
    items: Optional[List[SaleItemOut]] = []
    channel_name: Optional[str] = None
