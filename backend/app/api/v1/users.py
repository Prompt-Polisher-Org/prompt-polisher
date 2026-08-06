"""
api/v1/users.py — User profile and preferences endpoints.

Task: Week 3-4 / User & Preferences API (task.md lines 149-165)
  [x] GET  /api/v1/users/me               — get current user profile
  [x] PUT  /api/v1/users/me               — update profile (display name)
  [x] DELETE /api/v1/users/me             — account deactivation (soft-delete)
  [x] GET  /api/v1/users/me/preferences   — get preferences
  [x] PUT  /api/v1/users/me/preferences   — update preferences
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.users import (
    UserResponse,
    UpdateProfileRequest,
    PreferenceResponse,
    UpdatePreferenceRequest,
    VALID_TONES,
    VALID_VERBOSITY,
    VALID_TARGET_MODELS,
    VALID_DOMAINS,
)
from app.services.user_service import (
    update_user_profile,
    deactivate_user,
    get_or_create_preferences,
    update_preferences,
)

router = APIRouter(prefix="/users", tags=["Users"])


# ── Profile Endpoints ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )


@router.put("/me", response_model=UserResponse, summary="Update current user profile")
async def update_me(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's display name."""
    updated = await update_user_profile(db, current_user, full_name=payload.full_name)
    return UserResponse(
        id=str(updated.id),
        email=updated.email,
        full_name=updated.full_name,
        is_active=updated.is_active,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate (soft-delete) current user account",
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete: marks the account as inactive.
    The user will no longer be able to log in, but data is preserved.
    """
    await deactivate_user(db, current_user)
    return


# ── Preferences Endpoints ─────────────────────────────────────────────────────

@router.get(
    "/me/preferences",
    response_model=PreferenceResponse,
    summary="Get current user preferences",
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's prompt preferences (created with defaults if none exist)."""
    prefs = await get_or_create_preferences(db, current_user.id)
    return PreferenceResponse(
        tone=prefs.tone,
        verbosity=prefs.verbosity,
        target_model=prefs.target_model,
        domain=prefs.domain,
        custom_instructions=prefs.custom_instructions,
    )


@router.put(
    "/me/preferences",
    response_model=PreferenceResponse,
    summary="Update current user preferences",
)
async def put_preferences(
    payload: UpdatePreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update any subset of prompt preferences.
    Only the fields you send will be changed — others stay the same.
    Validates that field values belong to the allowed option sets.
    """
    # Validate field values (only if provided)
    errors = []
    if payload.tone and payload.tone not in VALID_TONES:
        errors.append(f"tone must be one of: {sorted(VALID_TONES)}")
    if payload.verbosity and payload.verbosity not in VALID_VERBOSITY:
        errors.append(f"verbosity must be one of: {sorted(VALID_VERBOSITY)}")
    if payload.target_model and payload.target_model not in VALID_TARGET_MODELS:
        errors.append(f"target_model must be one of: {sorted(VALID_TARGET_MODELS)}")
    if payload.domain and payload.domain not in VALID_DOMAINS:
        errors.append(f"domain must be one of: {sorted(VALID_DOMAINS)}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
        )

    prefs = await update_preferences(
        db,
        user_id=current_user.id,
        tone=payload.tone,
        verbosity=payload.verbosity,
        target_model=payload.target_model,
        domain=payload.domain,
        custom_instructions=payload.custom_instructions,
    )

    return PreferenceResponse(
        tone=prefs.tone,
        verbosity=prefs.verbosity,
        target_model=prefs.target_model,
        domain=prefs.domain,
        custom_instructions=prefs.custom_instructions,
    )
