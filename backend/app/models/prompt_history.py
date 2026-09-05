import uuid
from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class PromptHistory(Base):
    __tablename__ = "prompt_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    optimized_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metrics
    tokens_generated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
