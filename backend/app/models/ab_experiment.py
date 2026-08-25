"""
models/ab_experiment.py — A/B Testing database models.

Task: Week 9-10 / Model Validation (task.md lines 551-554)
  [x] Serve model version A and B simultaneously
  [x] Track which version generated each response
  [x] Compare user satisfaction metrics per version
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base


class ABExperiment(Base):
    """Defines an A/B test experiment between two model versions."""
    __tablename__ = "ab_experiments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model identifiers (checkpoint paths or version tags)
    model_a: Mapped[str] = mapped_column(String(255), nullable=False)
    model_b: Mapped[str] = mapped_column(String(255), nullable=False)

    # Traffic split: percentage of traffic to model B (0-100)
    traffic_pct_b: Mapped[int] = mapped_column(Integer, default=50)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ABResult(Base):
    """Tracks individual inference results tagged with the model version."""
    __tablename__ = "ab_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ab_experiments.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Which variant was served
    variant: Mapped[str] = mapped_column(String(1), nullable=False)  # "A" or "B"
    model_version: Mapped[str] = mapped_column(String(255), nullable=False)

    # The actual prompt and response
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance metrics
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_generated: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # User satisfaction (linked after feedback)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 or -1

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
