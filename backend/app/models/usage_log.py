import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Composite index for usage analytics: filter by endpoint over time
    __table_args__ = (
        Index("ix_usage_logs_endpoint_created", "endpoint", "created_at"),
    )
