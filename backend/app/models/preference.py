from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
import uuid

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    preferred_style: Mapped[str] = mapped_column(String(50), default="balanced") # creative, professional, concise
    