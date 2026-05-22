from pydantic import BaseModel
from typing import List, Optional


class UserSettingsOut(BaseModel):
    currency: str
    categories: List[str]
    expense_categories: List[str]
    material_units: List[str]
    low_stock_threshold: int

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    currency: Optional[str] = None
    categories: Optional[List[str]] = None
    expense_categories: Optional[List[str]] = None
    material_units: Optional[List[str]] = None
    low_stock_threshold: Optional[int] = None
