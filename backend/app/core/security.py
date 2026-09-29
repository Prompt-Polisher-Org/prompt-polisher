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

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# ── Password Hashing ─────────────────────────────────────────────────────────

# bcrypt is the gold-standard hashing algorithm for passwords.
#
# We call the `bcrypt` package directly rather than going through passlib:
# passlib 1.7.4 probes `bcrypt.__about__.__version__`, which bcrypt 4.1+ removed,
# and the resulting broken backend detection makes every hash() call fail with
# "password cannot be longer than 72 bytes" — i.e. registration and login break
# outright on a fresh install.

# bcrypt only ever considers the first 72 bytes of a password. It used to
# truncate silently; 5.x raises instead, so we truncate explicitly to keep the
# previous behaviour (and stay compatible with hashes created earlier).
_BCRYPT_MAX_BYTES = 72


def _encode(plain_password: str) -> bytes:
    """UTF-8 encode a password and clamp it to bcrypt's 72-byte input limit."""
    return plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt. Never store plain passwords."""
    return bcrypt.hashpw(_encode(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed or non-bcrypt hash in the database — treat as a failed login
        # rather than letting a 500 leak out of the auth endpoint.
        return False


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
