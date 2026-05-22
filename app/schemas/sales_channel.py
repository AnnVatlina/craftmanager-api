from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class SalesChannelCreate(BaseModel):
    name: str
    type: str = "лс"
    event_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class SalesChannelUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    event_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class SalesChannelOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    type: str
    event_date: Optional[date] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelSaleOut(BaseModel):
    id: UUID
    sale_date: date
    total_amount: Optional[Decimal] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class SalesChannelDetailOut(SalesChannelOut):
    sales: List[ChannelSaleOut] = []
    sales_count: int = 0
