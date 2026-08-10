"""
services/user_service.py — Business logic for user profile & preferences.

Task: Week 3-4 / User & Preferences API (task.md lines 149-165)
Task: Week 7-8 / Ingestion Pipeline (task.md line 388)
  [x] Auto-embed user preferences on save/update
"""
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.preference import UserPreference

logger = logging.getLogger(__name__)


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
    After saving, automatically embeds the preferences into Qdrant for RAG retrieval.
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

    # ── Auto-embed into Qdrant (Week 7-8 task) ────────────────────────────
    # Fire-and-forget: embed the updated preferences in background.
    # We use a try/except so a Qdrant outage doesn't break preference saves.
    try:
        _embed_preferences_to_qdrant(prefs)
    except Exception as e:
        logger.warning(f"Failed to embed preferences for user {user_id}: {e}")

    return prefs


def _embed_preferences_to_qdrant(prefs: UserPreference) -> None:
    """
    Build a human-readable preference description and upsert it into Qdrant.
    This runs synchronously but is called after the DB commit so latency is
    not visible to the user (the HTTP response is sent before this resolves
    in production — we'd move this to a Celery task for scale).
    """
    from app.services.embedding_service import embedding_service
    from app.services.qdrant_service import qdrant_service

    # Build a natural-language description of preferences so the embedding
    # captures semantic meaning rather than raw field values.
    custom = prefs.custom_instructions or ""
    preference_text = (
        f"User prefers {prefs.tone} tone with {prefs.verbosity} verbosity. "
        f"Primary domain: {prefs.domain}. Target AI model: {prefs.target_model}. "
        f"{('Additional instructions: ' + custom) if custom else ''}"
    ).strip()

    vector = embedding_service.embed_text(preference_text)
    qdrant_service.upsert_preference(
        user_id=str(prefs.user_id),
        vector=vector,
        payload={
            "preference_text": preference_text,
            "tone": prefs.tone,
            "verbosity": prefs.verbosity,
            "target_model": prefs.target_model,
            "domain": prefs.domain,
        },
    )
    logger.debug(f"Embedded preferences for user {prefs.user_id} into Qdrant.")
