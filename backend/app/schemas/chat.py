"""
schemas/chat.py — Pydantic request/response models for chat sessions and messages.
"""
from pydantic import BaseModel
from datetime import datetime

# ── Session Schemas ────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str = "New Polishing Session"

class SessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}

# ── Message Schemas ────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: str
    session_id: str
    raw_content: str
    polished_content: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
