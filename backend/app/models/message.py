import uuid
from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,  # Frequently filtered by session
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    polished_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Relationship back to session (avoids N+1 queries)
    session = relationship("ChatSession", back_populates="messages", lazy="selectin")

    # Composite index for the most common query: messages by session ordered by time
    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )