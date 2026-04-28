"""
Steps 8 & 9: Google + GitHub OAuth2 Endpoints
==============================================
GET /google           → Redirect user to Google login page
GET /google/callback  → Handle Google's callback, return PASETO tokens
GET /github           → Redirect user to GitHub login page
GET /github/callback  → Handle GitHub's callback, return PASETO tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.db.session import get_db
from app.models.user import User
from app.core.paseto import create_access_token, create_refresh_token
from app.core.config import settings

router = APIRouter()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GOOGLE OAUTH2 (Step 8)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/google")
async def google_login():
    """
    Step 1: User clicks "Login with Google" on your frontend.
    This redirects them to Google's consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured. Add GOOGLE_CLIENT_ID to your .env file.",
        )

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        "response_type=code&"
        "scope=openid%20email%20profile&"
        "access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    Step 2: Google sends the user back here with a one-time 'code'.
    We exchange that code for the user's email and profile info.
    """
    # 1. Exchange the code for an access token from Google
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange code with Google.",
        )

    token_data = token_response.json()
    google_access_token = token_data.get("access_token")

    # 2. Use the access token to get the user's profile from Google
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

    if user_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to fetch user info from Google.",
        )

    google_user = user_response.json()
    google_id = google_user.get("id")
    email = google_user.get("email")
    full_name = google_user.get("name")

    # 3. Find-or-create: check if this Google user already exists
    result = await db.execute(select(User).where(User.oauth_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Also check if someone registered with this email via password
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            # Link their existing account to Google
            user.oauth_id = google_id
            user.auth_provider = "google"
        else:
            # Brand new user — create account
            user = User(
                email=email,
                full_name=full_name,
                auth_provider="google",
                oauth_id=google_id,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

    # 4. Generate PASETO tokens and redirect to frontend
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Redirect to frontend with tokens in the URL
    frontend_url = (
        f"http://localhost:3000/auth/callback?"
        f"access_token={access_token}&"
        f"refresh_token={refresh_token}"
    )
    return RedirectResponse(url=frontend_url)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GITHUB OAUTH2 (Step 9)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/github")
async def github_login():
    """
    Step 1: User clicks "Login with GitHub" on your frontend.
    This redirects them to GitHub's authorization page.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth is not configured. Add GITHUB_CLIENT_ID to your .env file.",
        )

    github_auth_url = (
        "https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        "scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
async def github_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    Step 2: GitHub sends the user back here with a one-time 'code'.
    We exchange that code for the user's email and profile info.
    """
    # 1. Exchange the code for an access token from GitHub
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange code with GitHub.",
        )

    token_data = token_response.json()
    github_access_token = token_data.get("access_token")

    if not github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub did not return an access token.",
        )

    # 2. Get the user's profile from GitHub
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
        )

    if user_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to fetch user info from GitHub.",
        )

    github_user = user_response.json()
    github_id = str(github_user.get("id"))
    full_name = github_user.get("name") or github_user.get("login")

    # 3. GitHub doesn't always return email in the profile — fetch it separately
    async with httpx.AsyncClient() as client:
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
        )

    email = None
    if email_response.status_code == 200:
        emails = email_response.json()
        # Find the primary, verified email
        for e in emails:
            if e.get("primary") and e.get("verified"):
                email = e.get("email")
                break
        # Fallback: use the first email
        if not email and emails:
            email = emails[0].get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve email from GitHub. Make sure your email is public or verified.",
        )

    # 4. Find-or-create user
    result = await db.execute(select(User).where(User.oauth_id == github_id))
    user = result.scalar_one_or_none()

    if not user:
        # Check if someone registered with this email via password
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            # Link their existing account to GitHub
            user.oauth_id = github_id
            user.auth_provider = "github"
        else:
            # Brand new user
            user = User(
                email=email,
                full_name=full_name,
                auth_provider="github",
                oauth_id=github_id,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

    # 5. Generate PASETO tokens and redirect to frontend
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    frontend_url = (
        f"http://localhost:3000/auth/callback?"
        f"access_token={access_token}&"
        f"refresh_token={refresh_token}"
    )
    return RedirectResponse(url=frontend_url)
