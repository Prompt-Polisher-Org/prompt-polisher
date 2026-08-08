"""
services/oauth_service.py — OAuth 2.0 integration for Google and GitHub.

Handles:
- Building authorization URLs for each provider
- Exchanging authorization codes for user information
- Finding or creating users from OAuth data

Task: Week 3-4 / OAuth 2.0 Flow (task.md lines 141-145)
"""
import uuid
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User


# ── Google OAuth Constants ────────────────────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# ── GitHub OAuth Constants ────────────────────────────────────────────────────

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


# ── Google OAuth Flow ─────────────────────────────────────────────────────────

def get_google_auth_url() -> str:
    """
    Build the Google OAuth 2.0 consent screen URL.
    The user is redirected here to grant permission.
    """
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/google/callback"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_google_code(code: str) -> dict:
    """
    Exchange the authorization code from Google for user information.

    Steps:
    1. POST to Google's token endpoint with the code → get access_token
    2. GET Google's userinfo endpoint with the access_token → get user data

    Returns dict with keys: id, email, name
    """
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/google/callback"

    async with httpx.AsyncClient() as client:
        # Step 1: Exchange code for tokens
        token_response = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        })
        token_response.raise_for_status()
        tokens = token_response.json()

        # Step 2: Fetch user profile using the access token
        userinfo_response = await client.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

    return {
        "id": userinfo["id"],
        "email": userinfo["email"],
        "name": userinfo.get("name"),
    }


# ── GitHub OAuth Flow ─────────────────────────────────────────────────────────

def get_github_auth_url() -> str:
    """
    Build the GitHub OAuth authorization URL.
    The user is redirected here to grant permission.
    """
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/github/callback"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


async def exchange_github_code(code: str) -> dict:
    """
    Exchange the authorization code from GitHub for user information.

    Steps:
    1. POST to GitHub's token endpoint with the code → get access_token
    2. GET GitHub's user endpoint with the access_token → get user data
    3. GET GitHub's emails endpoint → get primary email (since email may be private)

    Returns dict with keys: id, email, name
    """
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/github/callback"

    async with httpx.AsyncClient() as client:
        # Step 1: Exchange code for access token
        token_response = await client.post(GITHUB_TOKEN_URL, data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        }, headers={"Accept": "application/json"})
        token_response.raise_for_status()
        tokens = token_response.json()
        access_token = tokens["access_token"]

        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        # Step 2: Fetch user profile
        user_response = await client.get(GITHUB_USER_URL, headers=auth_headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        # Step 3: Fetch primary email (GitHub users can hide their email)
        email = user_data.get("email")
        if not email:
            emails_response = await client.get(GITHUB_EMAILS_URL, headers=auth_headers)
            emails_response.raise_for_status()
            emails = emails_response.json()
            # Pick the primary verified email
            primary = next(
                (e for e in emails if e.get("primary") and e.get("verified")),
                emails[0] if emails else None
            )
            email = primary["email"] if primary else None

    return {
        "id": str(user_data["id"]),
        "email": email,
        "name": user_data.get("name") or user_data.get("login"),
    }


# ── User Lookup / Creation ───────────────────────────────────────────────────

async def get_user_by_oauth(db: AsyncSession, provider: str, oauth_id: str) -> User | None:
    """Find an existing user by their OAuth provider and provider-specific ID."""
    result = await db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_oauth_user(
    db: AsyncSession,
    provider: str,
    oauth_id: str,
    email: str,
    name: str | None,
) -> User:
    """
    Find an existing OAuth user or create a new one.

    Logic:
    1. First, look up by (oauth_provider, oauth_id) — exact match
    2. If not found, look up by email — maybe they registered with email/password first
       → If found, link the OAuth identity to their existing account
    3. If still not found, create a brand-new user
    """
    # 1. Try finding by OAuth identity
    user = await get_user_by_oauth(db, provider, oauth_id)
    if user:
        return user

    # 2. Try finding by email (link OAuth to existing account)
    from app.services.auth_service import get_user_by_email
    user = await get_user_by_email(db, email)
    if user:
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        await db.commit()
        await db.refresh(user)
        return user

    # 3. Create a new OAuth user (no password needed)
    new_user = User(
        id=uuid.uuid4(),
        email=email,
        full_name=name,
        hashed_password=None,  # OAuth users don't have a password
        is_active=True,
        oauth_provider=provider,
        oauth_id=oauth_id,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
