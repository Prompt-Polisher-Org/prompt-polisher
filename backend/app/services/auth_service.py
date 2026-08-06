"""
services/auth_service.py — Business logic for authentication.

Handles:
- Looking up users from the database
- Verifying credentials
- Creating users
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user record from the database by their email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Fetch a user record from the database by their UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Verify email and password.
    Returns the User object if credentials are valid, None otherwise.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(db: AsyncSession, email: str, password: str, full_name: str | None = None) -> User:
    """
    Register a new user.
    - Hashes the password before storing.
    - Raises ValueError if the email is already taken.
    """
    # Check for duplicate email first
    existing = await get_user_by_email(db, email)
    if existing:
        raise ValueError("A user with this email already exists.")

    new_user = User(
        id=uuid.uuid4(),
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
