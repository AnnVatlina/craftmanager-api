import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Column, String, Text, Numeric, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)  # материалы / инструменты / реклама / прочее
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    expense_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_expenses_user_id", "user_id"),
        Index("ix_expenses_expense_date", "expense_date"),
        Index("ix_expenses_category", "category"),
    )
