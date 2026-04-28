# 🔐 Authentication System Plan: PASETO + Multi-Provider Auth

> **Timeline**: Week 3-4 | **Owner**: `🗄️ BE` Team Member
> **Status**: 📋 Planned | **Backend**: FastAPI (Python)

---

## Why PASETO Instead of JWT?

| Problem with JWT | How PASETO Fixes It |
|---|---|
| Allows `"alg": "none"` — attacker can forge tokens | No algorithm choice. PASETO version dictates everything. |
| Algorithm confusion attacks (RS256 vs HS256) | One version = one algorithm. No confusion possible. |
| Developers can pick weak algorithms | Only modern, audited cryptography allowed |

**PASETO Version We Use**: `v4.local`
- `v4` = Latest version, uses modern crypto (XChaCha20-Poly1305)
- `local` = Symmetric key (our server both creates AND verifies tokens — perfect for us)

**Python Library**: `pyseto` ([PyPI](https://pypi.org/project/pyseto/))

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     USER TRIES TO LOG IN                     │
└─────────────┬────────────┬──────────┬──────────┬─────────────┘
              │            │          │          │
        ┌─────▼─────┐ ┌───▼───┐ ┌───▼───┐ ┌───▼────┐
        │ Email +   │ │Google │ │GitHub │ │ Magic  │
        │ Password  │ │OAuth2 │ │OAuth2 │ │ Link   │
        └─────┬─────┘ └───┬───┘ └───┬───┘ └───┬────┘
              │            │          │          │
              ▼            ▼          ▼          ▼
        ┌──────────────────────────────────────────┐
        │      PASETO TOKEN BACKBONE (shared)      │
        │  ┌─────────────┐  ┌───────────────────┐  │
        │  │Access Token │  │ Refresh Token     │  │
        │  │ (30 min)    │  │ (7 days, rotated) │  │
        │  └─────────────┘  └───────────────────┘  │
        └──────────────────┬───────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │      PROTECTED API ENDPOINTS             │
        │  get_current_user dependency validates   │
        │  the PASETO on every request             │
        └──────────────────────────────────────────┘
```

> **Key insight**: No matter HOW the user logs in, the backend always produces the same PASETO token pair. The frontend just stores and sends tokens — it never cares which login method was used.

---

## New Dependencies

Add to `backend/requirements.txt`:
```
passlib[bcrypt]           # Password hashing (bcrypt algorithm)
pyseto                    # PASETO token creation & verification
httpx                     # Async HTTP client (for OAuth2 callbacks)
itsdangerous              # Signed tokens for magic links
```

---

## New Environment Variables

Add to `backend/.env`:
```env
# PASETO
PASETO_SECRET_KEY=your-32-byte-secret-key-here-change-in-prod
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth2 (from https://console.cloud.google.com)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

# GitHub OAuth2 (from https://github.com/settings/developers)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/github/callback

# Magic Link
MAGIC_LINK_SECRET=your-magic-link-secret
MAGIC_LINK_EXPIRE_MINUTES=15
```

---

# Step-by-Step Implementation Guide

## Step 1: Update Config (`app/core/config.py`)

Add all the new env variables to your Pydantic Settings class:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # PASETO
    PASETO_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    # GitHub OAuth2
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/github/callback"

    # Magic Link
    MAGIC_LINK_SECRET: str = ""
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
```

---

## Step 2: Password Hashing (`app/core/security.py`) — [NEW FILE]

This file handles converting plain-text passwords into unreadable hashes.

```python
from passlib.context import CryptContext

# bcrypt is intentionally slow — if an attacker steals your DB,
# it would take them YEARS to crack bcrypt hashes vs seconds for MD5
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain text password matches the stored hash.
    Used during login: user sends "mypassword123",
    we compare it against the hash stored in the database.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password. NEVER store plain text passwords in the database.
    Used during registration: user sends "mypassword123",
    we store "$2b$12$LJ3m4ys..." in the database.
    """
    return pwd_context.hash(password)
```

**How to test manually** (in Python shell):
```python
from app.core.security import get_password_hash, verify_password

hashed = get_password_hash("mypassword123")
print(hashed)  # "$2b$12$LJ3m4ys..."  (random every time!)

print(verify_password("mypassword123", hashed))  # True
print(verify_password("wrongpassword", hashed))   # False
```

---

## Step 3: PASETO Token System (`app/core/paseto.py`) — [NEW FILE]

This is the backbone. Every auth provider ultimately calls these functions.

```python
import json
from datetime import datetime, timedelta, timezone
import pyseto
from pyseto import Key
from app.core.config import settings


def _get_key():
    """
    Create a symmetric key for PASETO v4.local.
    The secret key must be exactly 32 bytes.
    """
    secret = settings.PASETO_SECRET_KEY.encode("utf-8")[:32].ljust(32, b"\0")
    return Key.new(version=4, purpose="local", key=secret)


def create_access_token(user_id: str) -> str:
    """
    Create a short-lived token (30 min). Sent with every API request
    in the Authorization header: "Bearer v4.local.xxxxx..."
    """
    key = _get_key()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,                    # "subject" = who this token is for
        "type": "access",                  # so we don't confuse it with refresh
        "iat": now.isoformat(),            # "issued at"
        "exp": (now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat(),
    }
    token = pyseto.encode(key, payload=json.dumps(payload).encode("utf-8"))
    return token.decode("utf-8")


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived token (7 days). Only used to get a new
    access token when the old one expires. Stored securely by frontend.
    """
    key = _get_key()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now.isoformat(),
        "exp": (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
    }
    token = pyseto.encode(key, payload=json.dumps(payload).encode("utf-8"))
    return token.decode("utf-8")


def verify_token(token: str) -> dict:
    """
    Decode and verify a PASETO token. Returns the payload dict.
    Raises an exception if the token is invalid, tampered, or expired.
    """
    key = _get_key()
    decoded = pyseto.decode(key, token.encode("utf-8"))
    payload = json.loads(decoded.payload)

    # Check expiration manually
    exp = datetime.fromisoformat(payload["exp"])
    if datetime.now(timezone.utc) > exp:
        raise ValueError("Token has expired")

    return payload
```

**How to test manually**:
```python
from app.core.paseto import create_access_token, verify_token

token = create_access_token("user-uuid-123")
print(token)  # "v4.local.xxxxxxxxxxxxxxx..."

payload = verify_token(token)
print(payload)  # {"sub": "user-uuid-123", "type": "access", ...}
```

---

## Step 4: Pydantic Schemas (`app/schemas/auth.py`) — [NEW FILE]

These define the exact shape of request/response JSON bodies.

```python
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str          # minimum 8 characters (validate in endpoint)
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str
```

---

## Step 5: Update User Model (`app/models/user.py`) — [MODIFY]

Support all auth providers. Key change: `hashed_password` becomes **nullable** (Google/GitHub users don't have passwords).

```python
import uuid
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)  # NULL for OAuth users
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime, server_default=func.now())

    # NEW: Auth provider tracking
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")
    # Possible values: "email", "google", "github", "magic_link"

    oauth_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    # Google/GitHub's unique user ID — used to find returning OAuth users
```

After modifying this, run: `alembic revision --autogenerate -m "add auth provider fields"`

---

## Step 6: Auth Dependency (`app/api/v1/deps.py`) — [NEW FILE]

This is the "guard" function. Add it to any route that requires login.

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.paseto import verify_token
from app.db.session import get_session

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_session),
):
    """
    Extract user from PASETO token. Protects any route that uses it.
    Usage: current_user: User = Depends(get_current_user)
    """
    try:
        payload = verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use an access token.",
        )

    # Look up user in database
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    return user
```

---

## Step 7: Email + Password Endpoints (`app/api/v1/auth.py`) — [NEW FILE]

| Endpoint | Method | What it does |
|---|---|---|
| `/api/v1/auth/register` | POST | Hash password → save user → return PASETO pair |
| `/api/v1/auth/login` | POST | Verify email+password → return PASETO pair |
| `/api/v1/auth/refresh` | POST | Verify refresh token → issue new PASETO pair |
| `/api/v1/auth/logout` | POST | Blacklist refresh token in Redis |
| `/api/v1/auth/magic-link` | POST | Generate signed link → send email |
| `/api/v1/auth/magic-link/verify` | GET | Verify link → return PASETO pair |

**Detailed flow for Register:**
1. Frontend sends `{email, password, full_name}`
2. Check if email already exists in DB → if yes, return 409 Conflict
3. Hash the password with bcrypt
4. Create new User row in DB
5. Generate access + refresh PASETO tokens
6. Return `{access_token, refresh_token, token_type: "bearer"}`

**Detailed flow for Login:**
1. Frontend sends `{email, password}`
2. Find user by email → if not found, return 401
3. Verify password with bcrypt → if wrong, return 401
4. Generate PASETO pair → return it

**Token Rotation (Refresh):**
1. Frontend sends `{refresh_token}` when access token expires
2. Verify the refresh token → check it's type "refresh" and not expired
3. Generate a BRAND NEW access + refresh pair
4. Invalidate the old refresh token (add to Redis blacklist)
5. Return new pair

---

## Step 8: Google OAuth2 Endpoints (`app/api/v1/oauth.py`) — [NEW FILE]

| Endpoint | Method | What it does |
|---|---|---|
| `/api/v1/auth/oauth/google` | GET | Build Google URL → redirect user |
| `/api/v1/auth/oauth/google/callback` | GET | Exchange code → get user info → PASETO pair |

**Flow explained:**
1. User clicks "Sign in with Google" on your frontend
2. Frontend opens `localhost:8000/api/v1/auth/oauth/google`
3. Backend builds this URL and redirects:
   ```
   https://accounts.google.com/o/oauth2/auth?
     client_id=YOUR_ID&
     redirect_uri=localhost:8000/.../callback&
     scope=email+profile&
     response_type=code
   ```
4. User logs in on Google's page (we NEVER see their password)
5. Google redirects back to our `/callback` with a one-time `code`
6. Backend sends `code` + `client_secret` to Google's token API using `httpx`
7. Google returns user's email, name, and Google user ID
8. Backend does find-or-create:
   - If `oauth_id` exists in our DB → returning user → issue PASETO
   - If not → create new User with `auth_provider="google"`, `hashed_password=NULL`
9. Redirect to frontend with tokens: `localhost:3000/auth/callback?token=v4.local.xxx`

**To get Google credentials:**
1. Go to https://console.cloud.google.com
2. Create a project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Add `http://localhost:8000/api/v1/auth/oauth/google/callback` as authorized redirect URI
5. Copy Client ID and Client Secret to your `.env`

---

## Step 9: GitHub OAuth2 Endpoints (same file as Step 8)

Exact same pattern as Google, different URLs:

| GitHub Endpoint | URL |
|---|---|
| Authorization | `https://github.com/login/oauth/authorize` |
| Token Exchange | `https://github.com/login/oauth/access_token` |
| User Info | `https://api.github.com/user` |

**To get GitHub credentials:**
1. Go to https://github.com/settings/developers
2. New OAuth App
3. Set callback URL to `http://localhost:8000/api/v1/auth/oauth/github/callback`
4. Copy Client ID and Client Secret to your `.env`

---

## Step 10: Magic Link Endpoints (in `app/api/v1/auth.py`)

**Flow:**
1. User enters email → clicks "Send Magic Link"
2. Backend generates a cryptographically signed token using `itsdangerous`:
   ```python
   from itsdangerous import URLSafeTimedSerializer
   s = URLSafeTimedSerializer(settings.MAGIC_LINK_SECRET)
   token = s.dumps(email, salt="magic-link")
   ```
3. Backend sends email: "Click here: `localhost:3000/auth/verify?token=xxx`"
4. User clicks link → frontend sends token to `/magic-link/verify`
5. Backend verifies signature + checks expiry (15 min):
   ```python
   email = s.loads(token, salt="magic-link", max_age=900)  # 900 seconds = 15 min
   ```
6. Find-or-create user → issue PASETO pair

> For email sending, use **Resend** (free tier: 100 emails/day) or **SendGrid** (free tier: 100 emails/day). Enough for a demo.

---

## Step 11: Wire Routers in `app/main.py`

```python
from app.api.v1.auth import router as auth_router
from app.api.v1.oauth import router as oauth_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(oauth_router, prefix="/api/v1/auth/oauth", tags=["OAuth"])
```

---

## Implementation Order

| # | Task | File(s) | Depends On |
|---|---|---|---|
| 1 | Install deps + update config | `requirements.txt`, `config.py`, `.env` | Nothing |
| 2 | Password hashing utility | `core/security.py` | Step 1 |
| 3 | PASETO token backbone | `core/paseto.py` | Step 1 |
| 4 | Pydantic schemas | `schemas/auth.py` | Nothing |
| 5 | Update User model + migration | `models/user.py` | Step 1 |
| 6 | `get_current_user` dependency | `api/v1/deps.py` | Steps 3, 5 |
| 7 | Email+Password endpoints | `api/v1/auth.py` | Steps 2-6 |
| 8 | Google OAuth2 | `api/v1/oauth.py` | Steps 3, 6 |
| 9 | GitHub OAuth2 | `api/v1/oauth.py` | Steps 3, 6 |
| 10 | Magic Link endpoints | `api/v1/auth.py` | Steps 3, 6 |
| 11 | Wire routers | `main.py` | Steps 7-10 |
| 12 | Tests | `tests/test_auth.py` | Step 11 |

---

## Verification Plan

Open `http://localhost:8000/docs` (Swagger UI) and test:
1. `POST /register` with email+password → should return PASETO tokens
2. `POST /login` with correct password → tokens returned
3. `POST /login` with wrong password → 401 error
4. `GET /oauth/google` → redirects to Google login page
5. `POST /magic-link` → returns success message
6. Access protected route WITHOUT token → 401
7. Access protected route WITH valid token → user data returned
8. Use expired token → 401, then `/refresh` works
