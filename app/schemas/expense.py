from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


class ExpenseCreate(BaseModel):
    category: str
    amount: Decimal
    description: Optional[str] = None
    expense_date: date


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None


class ExpenseOut(BaseModel):
    id: UUID
    user_id: UUID
    category: str
    amount: Decimal
    description: Optional[str] = None
    expense_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
