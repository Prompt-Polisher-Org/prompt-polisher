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
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
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
        message="Registration successful! Please log in.",
        # User.id is a uuid.UUID and UserResponse.id is a str; pydantic v2 does
        # not coerce between them, so convert explicitly (as the other routers do).
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
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


# ── OAuth 2.0 — Google and GitHub ─────────────────────────────────────────────

def _state_cookie_name(provider: str) -> str:
    return f"prompt_polisher_oauth_{provider}_state"


def _callback_path(provider: str) -> str:
    return f"/api/v1/auth/oauth/{provider}/callback"


def _start_oauth(
    provider: str,
    client_id: str,
    client_secret: str,
    auth_url_builder,
) -> RedirectResponse:
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{provider.title()} OAuth is not configured. Set its client ID and secret in the backend environment.",
        )

    state = secrets.token_urlsafe(32)
    response = RedirectResponse(url=auth_url_builder(state), status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=_state_cookie_name(provider),
        value=state,
        max_age=600,
        httponly=True,
        secure=settings.OAUTH_REDIRECT_BASE_URL.lower().startswith("https://"),
        samesite="lax",
        path=_callback_path(provider),
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def _finish_oauth(
    provider: str,
    tokens: TokenResponse | None = None,
    error: str | None = None,
) -> RedirectResponse:
    callback_url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback"
    if tokens:
        fragment = urlencode({
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
        })
        destination = f"{callback_url}#{fragment}"
    else:
        destination = f"{callback_url}?error={error or 'oauth_failed'}"

    response = RedirectResponse(url=destination, status_code=status.HTTP_302_FOUND)
    response.delete_cookie(
        key=_state_cookie_name(provider),
        path=_callback_path(provider),
        secure=settings.OAUTH_REDIRECT_BASE_URL.lower().startswith("https://"),
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def _state_is_valid(request: Request, provider: str, state: str | None) -> bool:
    cookie_state = request.cookies.get(_state_cookie_name(provider))
    return bool(cookie_state and state and secrets.compare_digest(cookie_state, state))


@router.get("/oauth/google", summary="Redirect to Google OAuth consent screen")
async def oauth_google_redirect():
    return _start_oauth(
        "google",
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        get_google_auth_url,
    )


@router.get("/oauth/google/callback", summary="Handle Google OAuth callback")
async def oauth_google_callback(
    request: Request,
    code: str | None = Query(None, description="Authorization code from Google"),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if not _state_is_valid(request, "google", state):
        return _finish_oauth("google", error="oauth_state_mismatch")
    if error or not code:
        return _finish_oauth("google", error="google_sign_in_cancelled")

    try:
        google_user = await exchange_google_code(code)
        if not google_user.get("email") or not google_user.get("email_verified"):
            return _finish_oauth("google", error="google_email_not_verified")
        user = await get_or_create_oauth_user(
            db,
            provider="google",
            oauth_id=google_user["id"],
            email=google_user["email"],
            name=google_user.get("name"),
        )
        tokens = TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
        return _finish_oauth("google", tokens=tokens)
    except Exception:
        logger.exception("Google OAuth callback failed")
        return _finish_oauth("google", error="google_sign_in_failed")


@router.get("/oauth/github", summary="Redirect to GitHub OAuth consent screen")
async def oauth_github_redirect():
    return _start_oauth(
        "github",
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        get_github_auth_url,
    )


@router.get("/oauth/github/callback", summary="Handle GitHub OAuth callback")
async def oauth_github_callback(
    request: Request,
    code: str | None = Query(None, description="Authorization code from GitHub"),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if not _state_is_valid(request, "github", state):
        return _finish_oauth("github", error="oauth_state_mismatch")
    if error or not code:
        return _finish_oauth("github", error="github_sign_in_cancelled")

    try:
        github_user = await exchange_github_code(code)
        if not github_user.get("email") or not github_user.get("email_verified"):
            return _finish_oauth("github", error="github_email_not_verified")
        user = await get_or_create_oauth_user(
            db,
            provider="github",
            oauth_id=github_user["id"],
            email=github_user["email"],
            name=github_user.get("name"),
        )
        tokens = TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
        return _finish_oauth("github", tokens=tokens)
    except Exception:
        logger.exception("GitHub OAuth callback failed")
        return _finish_oauth("github", error="github_sign_in_failed")
