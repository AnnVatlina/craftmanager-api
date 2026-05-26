from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID


class FairItemAdd(BaseModel):
    product_id: UUID
    planned_qty: int


class FairItemUpdate(BaseModel):
    planned_qty: int


class FairItemOut(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    category: Optional[str] = None
    sale_price: Decimal
    planned_qty: int
    stock_qty: int
    need_to_make: int  # max(0, planned_qty - stock_qty), computed server-side

    model_config = {"from_attributes": True}


class FairChannelRef(BaseModel):
    id: UUID
    name: str
    event_date: Optional[date] = None
    location: Optional[str] = None


class FairPrepSummary(BaseModel):
    total_positions: int       # number of distinct products
    total_planned: int         # sum of all planned_qty
    total_need_to_make: int    # sum of all need_to_make


class FairPrepOut(BaseModel):
    channel: FairChannelRef
    items: List[FairItemOut]
    summary: FairPrepSummary
