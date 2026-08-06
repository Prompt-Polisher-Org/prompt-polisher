"""
schemas/feedback.py — Pydantic models for user feedback on AI responses.
"""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class FeedbackCreate(BaseModel):
    message_id: UUID
    rating: int  # 1 for upvote, -1 for downvote
    comment: str | None = None

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
