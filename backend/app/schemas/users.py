"""
schemas/users.py — Pydantic request/response models for the Users & Preferences API.

Task: Week 3-4 / User & Preferences API (task.md lines 149-165)
"""
from pydantic import BaseModel


# ── User schemas ──────────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    """Body for PUT /api/v1/users/me"""
    full_name: str | None = None

    model_config = {"json_schema_extra": {"example": {"full_name": "Alice Smith"}}}


class UserResponse(BaseModel):
    """Safe user profile — no password hash."""
    id: str
    email: str
    full_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Preference schemas ─────────────────────────────────────────────────────────

VALID_TONES = {"professional", "casual", "academic", "creative"}
VALID_VERBOSITY = {"concise", "detailed", "balanced"}
VALID_TARGET_MODELS = {"GPT-4", "Claude", "Gemini", "General"}
VALID_DOMAINS = {"marketing", "coding", "writing", "general"}


class PreferenceResponse(BaseModel):
    """Full preference object returned to the client."""
    tone: str
    verbosity: str
    target_model: str
    domain: str
    custom_instructions: str | None

    model_config = {"from_attributes": True}


class UpdatePreferenceRequest(BaseModel):
    """
    Body for PUT /api/v1/users/me/preferences.
    All fields are optional — only send the ones you want to change.
    """
    tone: str | None = None
    verbosity: str | None = None
    target_model: str | None = None
    domain: str | None = None
    custom_instructions: str | None = None

    model_config = {"json_schema_extra": {
        "example": {
            "tone": "casual",
            "verbosity": "concise",
            "target_model": "GPT-4",
            "domain": "coding",
            "custom_instructions": "Always add code examples."
        }
    }}
