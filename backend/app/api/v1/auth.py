"""
Step 7 & 10: Email+Password Auth + Magic Link Endpoints
========================================================
POST /register      → Create account with email+password
POST /login         → Verify credentials, return PASETO tokens
POST /refresh       → Exchange refresh token for new token pair
POST /magic-link    → Generate and "send" a magic link
GET  /magic-link/verify → Verify the magic link, return tokens
GET  /me            → Return current user info (protected)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    MagicLinkRequest,
    MessageResponse,
)
from app.core.security import get_password_hash, verify_password
from app.core.paseto import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.api.v1.deps import get_current_user

router = APIRouter()


# ──────────────────────────────────────────
#  POST /register
# ──────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new user account with email and password.
    Returns a PASETO access + refresh token pair.
    """
    # 1. Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # 2. Validate password length
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )

    # 3. Hash the password and create the user
    new_user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=get_password_hash(request.password),
        auth_provider="email",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # 4. Generate PASETO tokens
    access_token = create_access_token(str(new_user.id))
    refresh_token = create_refresh_token(str(new_user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ──────────────────────────────────────────
#  POST /login
# ──────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with email + password.
    Returns a PASETO access + refresh token pair.
    """
    # 1. Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # 2. If user not found OR password doesn't match → 401
    #    We use the same error message for both to prevent "email enumeration"
    #    (an attacker shouldn't know which emails exist in your system)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 3. Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # 4. Generate PASETO tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ──────────────────────────────────────────
#  POST /refresh
# ──────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange a valid refresh token for a brand new access + refresh token pair.
    This is called silently by the frontend when the access token expires.
    """
    try:
        payload = verify_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Make sure it's actually a refresh token, not an access token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected a refresh token.",
        )

    # Verify the user still exists and is active
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )

    # Issue a brand new pair (token rotation)
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ──────────────────────────────────────────
#  POST /magic-link  (Step 10)
# ──────────────────────────────────────────
@router.post("/magic-link", response_model=MessageResponse)
async def request_magic_link(request: MagicLinkRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a magic link for passwordless login.
    In production, this would send an email. For now, we return the link
    in the response so you can test it.
    """
    # Generate a signed, time-limited token using itsdangerous
    serializer = URLSafeTimedSerializer(settings.MAGIC_LINK_SECRET)
    token = serializer.dumps(request.email, salt="magic-link")

    # In production: send this link via email (e.g., Resend, SendGrid)
    # For development/testing, we return it directly in the response
    magic_url = f"http://localhost:3000/auth/verify?token={token}"

    return MessageResponse(
        message=f"Magic link generated (dev mode). Use this link: {magic_url}"
    )


# ──────────────────────────────────────────
#  GET /magic-link/verify
# ──────────────────────────────────────────
@router.get("/magic-link/verify", response_model=TokenResponse)
async def verify_magic_link(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    Verify a magic link token and return PASETO tokens.
    The token is valid for MAGIC_LINK_EXPIRE_MINUTES (default: 15 min).
    """
    serializer = URLSafeTimedSerializer(settings.MAGIC_LINK_SECRET)

    try:
        # max_age is in seconds: 15 min × 60 = 900 seconds
        email = serializer.loads(
            token,
            salt="magic-link",
            max_age=settings.MAGIC_LINK_EXPIRE_MINUTES * 60,
        )
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Magic link has expired. Please request a new one.",
        )
    except BadSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid magic link.",
        )

    # Find or create the user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # First time using magic link = auto-register
        user = User(
            email=email,
            auth_provider="magic_link",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate PASETO tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ──────────────────────────────────────────
#  GET /me  (Protected route example)
# ──────────────────────────────────────────
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently logged-in user's info.
    This endpoint is PROTECTED — it requires a valid PASETO access token.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "auth_provider": current_user.auth_provider,
        "is_active": current_user.is_active,
    }
