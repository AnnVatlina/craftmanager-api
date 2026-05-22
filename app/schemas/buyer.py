from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class BuyerCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    notes: Optional[str] = None


class BuyerUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    notes: Optional[str] = None


class BuyerOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    contact: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BuyerSaleOut(BaseModel):
    id: UUID
    sale_date: date
    total_amount: Optional[Decimal] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class BuyerDetailOut(BuyerOut):
    sales: List[BuyerSaleOut] = []
    sales_count: int = 0
