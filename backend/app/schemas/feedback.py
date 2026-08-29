"""
schemas/feedback.py — Pydantic models for user feedback on AI responses.
"""
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class FeedbackCreate(BaseModel):
    message_id: UUID
    rating: Literal[1, -1]  # Strictly 1 (thumbs up) or -1 (thumbs down)
    comment: str | None = Field(None, max_length=1000)

class FeedbackResponse(BaseModel):
    id: UUID
    message_id: UUID
    user_id: UUID
    rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

class FeedbackStats(BaseModel):
    total_feedback: int
    upvotes: int
    downvotes: int
    positive_ratio: float
