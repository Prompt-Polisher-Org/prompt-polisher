import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,  # Frequently filtered by user
    )
    title: Mapped[str] = mapped_column(String(255), default="New Polishing Session")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Relationship to messages (eager-loaded via selectin to avoid N+1)
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", lazy="selectin",
        cascade="all, delete-orphan", order_by="Message.created_at",
    )

    # Composite index for the most common query: sessions by user ordered by time
    __table_args__ = (
        Index("ix_chat_sessions_user_created", "user_id", "created_at"),
    )