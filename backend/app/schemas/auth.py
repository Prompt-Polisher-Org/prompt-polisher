"""
schemas/auth.py — Pydantic request/response models for the auth system.

These define the shape of data that comes IN (requests) and goes OUT (responses)
for all authentication endpoints.
"""
from pydantic import BaseModel, EmailStr


# ── Request Schemas (what the client sends) ───────────────────────────────────

class RegisterRequest(BaseModel):
    """Body for POST /api/v1/auth/register"""
    email: EmailStr
    password: str
    full_name: str | None = None

    model_config = {"json_schema_extra": {
        "example": {
            "email": "alice@example.com",
            "password": "SecurePass123!",
            "full_name": "Alice Smith"
        }
    }}


class LoginRequest(BaseModel):
    """Body for POST /api/v1/auth/login"""
    email: EmailStr
    password: str

    model_config = {"json_schema_extra": {
        "example": {
            "email": "alice@example.com",
            "password": "SecurePass123!"
        }
    }}


class RefreshRequest(BaseModel):
    """Body for POST /api/v1/auth/refresh"""
    refresh_token: str


# ── Response Schemas (what the server returns) ────────────────────────────────

class TokenResponse(BaseModel):
    """Returned after a successful login or token refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Safe user representation — never exposes password hash."""
    id: str
    email: str
    full_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    """Returned after a successful registration."""
    message: str
    user: UserResponse
