from pydantic import BaseModel
from typing import Optional
from datetime import datetime
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
