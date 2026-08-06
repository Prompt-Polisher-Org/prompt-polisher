"""
api/v1/auth.py — Authentication endpoints.

Task: Week 3-4 / Authentication System (task.md lines 136-145)
  [x] POST /api/v1/auth/register  — email + password registration
  [x] POST /api/v1/auth/login     — returns access + refresh tokens
  [x] POST /api/v1/auth/refresh   — refresh token rotation
  [x] POST /api/v1/auth/logout    — (stateless: client discards token)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.services.auth_service import authenticate_user, create_user, get_user_by_id
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    RegisterResponse,
    UserResponse,
)
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user with email + password.
    - Password is hashed with bcrypt before storage.
    - Returns the created user profile (no password in response).
    - Raises 409 if the email is already registered.
    """
    try:
        user = await create_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return RegisterResponse(
        message="Registration successful! Please log in.",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive JWT tokens",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with email and password.
    Returns a short-lived access token (30 min) and a long-lived refresh token (7 days).
    Store both securely in the client (preferably httpOnly cookies in production).
    """
    user = await authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        # Use a generic message to avoid leaking whether the email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Get a new access token using a refresh token",
)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange a valid refresh token for a fresh access token + new refresh token.
    (Refresh token rotation: each use yields a new refresh token)
    Raises 401 if the refresh token is expired or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = decode_token(payload.refresh_token)
        user_id: str | None = token_data.get("sub")
        token_type: str | None = token_data.get("type")

        if user_id is None or token_type != "refresh":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    # Issue a fresh pair of tokens (rotation)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (client should discard tokens)",
)
async def logout():
    """
    Stateless logout.
    Because JWTs are self-contained, true server-side invalidation requires a
    token blacklist (Redis). For now, the client simply discards both tokens.
    In Week 11-12 (security audit), Redis blacklisting should be added.
    """
    # 204 No Content — nothing to return
    return
