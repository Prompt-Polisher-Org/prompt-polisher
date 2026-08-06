"""
security.py — Password hashing and JWT token utilities.

Task: Week 3-4 / Authentication System (task.md lines 131-135)
  [x] Implement password hashing utility (bcrypt)
  [x] Implement JWT token creation + verification (python-jose)
      [x] Access token generation (30 min expiry)
      [x] Refresh token generation (7 day expiry)
      [x] Token verification utility
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ─────────────────────────────────────────────────────────

# bcrypt is the gold-standard hashing algorithm for passwords.
# The CryptContext handles all hashing and verification.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt. Never store plain passwords."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token Creation ────────────────────────────────────────────────────────

def _create_token(subject: Any, token_type: str, expires_delta: timedelta) -> str:
    """
    Internal helper: encode a JWT with a subject, type, and expiry.
    `subject` is typically the user's UUID (as a string).
    """
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(subject),  # subject (user id)
        "type": token_type,   # "access" or "refresh"
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: Any) -> str:
    """
    Create a short-lived JWT access token (30 min by default).
    Used in Authorization: Bearer <token> headers for every API call.
    """
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, token_type="access", expires_delta=expires)


def create_refresh_token(subject: Any) -> str:
    """
    Create a long-lived JWT refresh token (7 days by default).
    Used ONLY to obtain a new access token when the old one expires.
    """
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, token_type="refresh", expires_delta=expires)


# ── JWT Token Verification ───────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Returns the payload dict on success.
    Raises JWTError if the token is invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
