"""
models/preference.py — UserPreference SQLAlchemy ORM model.

Task: Week 3-4 / User & Preferences API (task.md lines 158-163)
  [x] tone (professional, casual, academic, creative)
  [x] verbosity (concise, detailed, balanced)
  [x] target_model (GPT-4, Claude, Gemini, General)
  [x] domain (marketing, coding, writing, general)
  [x] custom_instructions (free text)
"""
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Preference fields (all have sensible defaults so new users get a working config)
    tone: Mapped[str] = mapped_column(String(50), default="professional")
    # options: professional | casual | academic | creative

    verbosity: Mapped[str] = mapped_column(String(50), default="balanced")
    # options: concise | detailed | balanced

    target_model: Mapped[str] = mapped_column(String(50), default="General")
    # options: GPT-4 | Claude | Gemini | General

    domain: Mapped[str] = mapped_column(String(50), default="general")
    # options: marketing | coding | writing | general

    custom_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Free-text field for any extra instructions

    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())