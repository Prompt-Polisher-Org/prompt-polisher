"""
services/user_service.py — Business logic for user profile & preferences.

Task: Week 3-4 / User & Preferences API (task.md lines 149-165)
"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.preference import UserPreference


# ── User CRUD ─────────────────────────────────────────────────────────────────

async def update_user_profile(
    db: AsyncSession,
    user: User,
    full_name: str | None,
) -> User:
    """Update the user's display name. Only updates fields that are not None."""
    if full_name is not None:
        user.full_name = full_name
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user: User) -> None:
    """
    Soft-delete: mark user as inactive instead of hard-deleting.
    This preserves data integrity for foreign key references.
    """
    user.is_active = False
    await db.commit()


# ── Preferences CRUD ──────────────────────────────────────────────────────────

async def get_or_create_preferences(db: AsyncSession, user_id: uuid.UUID) -> UserPreference:
    """
    Fetch the user's preferences row. If none exists yet, create one with defaults.
    This ensures every user always has a preferences object.
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if prefs is None:
        # First time: create default preferences for this user
        prefs = UserPreference(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return prefs


async def update_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
    tone: str | None = None,
    verbosity: str | None = None,
    target_model: str | None = None,
    domain: str | None = None,
    custom_instructions: str | None = None,
) -> UserPreference:
    """
    Update only the preference fields that are provided (not None).
    Uses get_or_create so new users can set preferences without a pre-existing row.
    """
    prefs = await get_or_create_preferences(db, user_id)

    if tone is not None:
        prefs.tone = tone
    if verbosity is not None:
        prefs.verbosity = verbosity
    if target_model is not None:
        prefs.target_model = target_model
    if domain is not None:
        prefs.domain = domain
    if custom_instructions is not None:
        prefs.custom_instructions = custom_instructions

    await db.commit()
    await db.refresh(prefs)
    return prefs
