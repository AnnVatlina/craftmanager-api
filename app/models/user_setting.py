import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    currency = Column(String, nullable=False, default="Br")
    categories = Column(Text, nullable=False, default="Вязаные игрушки плюш,Вязаные игрушки акрил,Лотерейные игрушки,Брелоки")
    low_stock_threshold = Column(Integer, nullable=False, default=5)
