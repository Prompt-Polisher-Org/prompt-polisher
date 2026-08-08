"""
api/v1/auth.py — Authentication endpoints (email/password + OAuth 2.0).

Task: Week 3-4 / Authentication System (task.md lines 131-147)
  [x] POST /api/v1/auth/register           — email + password registration
  [x] POST /api/v1/auth/login              — returns access + refresh tokens
  [x] POST /api/v1/auth/refresh            — refresh token rotation
  [x] POST /api/v1/auth/logout             — blacklist refresh token (stub)
  [x] GET  /api/v1/auth/oauth/google       — redirect to Google
  [x] GET  /api/v1/auth/oauth/google/callback — handle Google callback
  [x] GET  /api/v1/auth/oauth/github       — redirect to GitHub
  [x] GET  /api/v1/auth/oauth/github/callback — handle GitHub callback
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.services.auth_service import authenticate_user, create_user
from app.services.oauth_service import (
    get_google_auth_url,
    exchange_google_code,
    get_github_auth_url,
    exchange_github_code,
    get_or_create_oauth_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Email / Password Auth ─────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new user with email + password")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account. Returns the user object on success."""
    try:
        user = await create_user(db, email=body.email, password=body.password, full_name=body.full_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return RegisterResponse(
        message="Registration successful!",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="Login with email + password")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Verify credentials and return JWT access + refresh tokens."""
    user = await authenticate_user(db, email=body.email, password=body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh(body: RefreshRequest):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/logout", status_code=status.HTTP_200_OK, summary="Logout (invalidate refresh token)")
async def logout():
    """
    Logout endpoint stub.
    In a production system this would blacklist the refresh token in Redis.
    For now, the client simply discards its tokens.
    """
    return {"message": "Logged out successfully. Please discard your tokens."}


# ── OAuth 2.0 — Google ────────────────────────────────────────────────────────

@router.get("/oauth/google", summary="Redirect to Google OAuth consent screen")
async def oauth_google_redirect():
    """
    Initiates the Google OAuth 2.0 flow.
    Redirects the user's browser to Google's consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )
    return RedirectResponse(url=get_google_auth_url())


@router.get("/oauth/google/callback", response_model=TokenResponse,
            summary="Handle Google OAuth callback")
async def oauth_google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: AsyncSession = Depends(get_db),
):
    """
    Google redirects here after the user grants permission.
    Exchanges the authorization code for user info, then creates or finds
    the user and returns JWT tokens.
    """
    try:
        google_user = await exchange_google_code(code)
    except Exception as e:
        logger.error(f"Google OAuth exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {e}",
        )

    if not google_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from Google account.",
        )

    user = await get_or_create_oauth_user(
        db,
        provider="google",
        oauth_id=google_user["id"],
        email=google_user["email"],
        name=google_user.get("name"),
    )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


# ── OAuth 2.0 — GitHub ────────────────────────────────────────────────────────

@router.get("/oauth/github", summary="Redirect to GitHub OAuth consent screen")
async def oauth_github_redirect():
    """
    Initiates the GitHub OAuth flow.
    Redirects the user's browser to GitHub's authorization page.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env",
        )
    return RedirectResponse(url=get_github_auth_url())


@router.get("/oauth/github/callback", response_model=TokenResponse,
            summary="Handle GitHub OAuth callback")
async def oauth_github_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    db: AsyncSession = Depends(get_db),
):
    """
    GitHub redirects here after the user grants permission.
    Exchanges the authorization code for user info, then creates or finds
    the user and returns JWT tokens.
    """
    try:
        github_user = await exchange_github_code(code)
    except Exception as e:
        logger.error(f"GitHub OAuth exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with GitHub: {e}",
        )

    if not github_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from GitHub account. Ensure your email is public or grant the user:email scope.",
        )

    user = await get_or_create_oauth_user(
        db,
        provider="github",
        oauth_id=github_user["id"],
        email=github_user["email"],
        name=github_user.get("name"),
    )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
