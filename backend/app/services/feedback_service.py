"""
services/feedback_service.py — Business logic for RLHF feedback and analytics.
"""
import uuid
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.models.feedback import Feedback
from app.models.message import Message
from app.schemas.feedback import FeedbackStats

async def create_feedback(db: AsyncSession, user_id: uuid.UUID, message_id: uuid.UUID, rating: int, comment: str | None = None) -> Feedback:
    # Optional: check if feedback already exists and update it, or just create new. We will just create new or update if one exists.
    result = await db.execute(select(Feedback).where(Feedback.user_id == user_id, Feedback.message_id == message_id))
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.rating = rating
        existing.comment = comment
        await db.commit()
        await db.refresh(existing)
        return existing
        
    feedback = Feedback(id=uuid.uuid4(), user_id=user_id, message_id=message_id, rating=rating, comment=comment)
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback

async def get_feedback_stats(db: AsyncSession) -> FeedbackStats:
    result = await db.execute(
        select(
            func.count(Feedback.id).label("total"),
            func.sum(case((Feedback.rating == 1, 1), else_=0)).label("upvotes"),
            func.sum(case((Feedback.rating == -1, 1), else_=0)).label("downvotes")
        )
    )
    row = result.first()
    if not row or row.total == 0:
        return FeedbackStats(total_feedback=0, upvotes=0, downvotes=0, positive_ratio=0.0)
    
    total = row.total
    up = int(row.upvotes or 0)
    down = int(row.downvotes or 0)
    ratio = up / total if total > 0 else 0.0
    
    return FeedbackStats(total_feedback=total, upvotes=up, downvotes=down, positive_ratio=ratio)

async def export_rlhf_data(db: AsyncSession) -> str:
    """
    Exports feedback as (prompt, chosen, rejected) pairs in CSV format.
    In a real system, 'chosen' is the optimized output. If it was downvoted, it might be the 'rejected' response.
    Here we export: raw_content (prompt), polished_content, rating (1 for chosen, -1 for rejected).
    """
    result = await db.execute(
        select(Message.raw_content, Message.polished_content, Feedback.rating)
        .join(Feedback, Message.id == Feedback.message_id)
        .where(Message.polished_content.is_not(None))
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["prompt", "response", "rating", "label"])
    
    for row in result:
        prompt, response, rating = row
        label = "chosen" if rating == 1 else "rejected"
        writer.writerow([prompt, response, rating, label])
        
    return output.getvalue()
