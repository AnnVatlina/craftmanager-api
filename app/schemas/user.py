from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    password: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
