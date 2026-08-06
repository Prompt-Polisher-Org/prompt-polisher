"""
api/v1/feedback.py — Endpoints for submitting and exporting RLHF feedback.

Task: Week 11-12 / Feedback System (task.md lines 575-583)
  [x] POST /api/v1/feedback
  [x] GET  /api/v1/feedback/stats
  [x] GET  /api/v1/feedback/export
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackStats
from app.services import feedback_service

router = APIRouter(prefix="/feedback", tags=["Feedback & Analytics"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a thumbs up / thumbs down feedback on a message."""
    if payload.rating not in (1, -1):
        raise HTTPException(status_code=422, detail="Rating must be 1 (upvote) or -1 (downvote)")
        
    feedback = await feedback_service.create_feedback(
        db, current_user.id, payload.message_id, payload.rating, payload.comment
    )
    return FeedbackResponse.model_validate(feedback)


@router.get("/stats", response_model=FeedbackStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated feedback stats. In production, this might be restricted to admins."""
    stats = await feedback_service.get_feedback_stats(db)
    return stats


@router.get("/export", response_class=PlainTextResponse)
async def export_rlhf(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export feedback as CSV triples (prompt, response, rating, label) for DPO/RLHF training."""
    csv_data = await feedback_service.export_rlhf_data(db)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rlhf_data.csv"}
    )
