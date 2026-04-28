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