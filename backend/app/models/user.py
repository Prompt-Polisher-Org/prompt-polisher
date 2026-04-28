import uuid
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)  # NULL for OAuth users
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, server_default=func.now())

    # NEW: Auth provider tracking
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")
    # Possible values: "email", "google", "github", "magic_link"

    oauth_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    # Google/GitHub's unique user ID — used to find returning OAuth users