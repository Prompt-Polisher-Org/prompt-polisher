"""
api/v1/chat.py — Endpoints for chat sessions and messages.

Task: Week 5-6 / Backend Inference Integration (task.md lines 330-336)
  [x] POST /api/v1/chat/sessions
  [x] GET  /api/v1/chat/sessions
  [x] GET  /api/v1/chat/sessions/{id}
  [x] GET  /api/v1/chat/sessions/{id}/messages
  [x] DELETE /api/v1/chat/sessions/{id}
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import SessionCreate, SessionResponse, MessageResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    session = await chat_service.create_session(db, current_user.id, payload.title)
    # Convert UUIDs to strings manually since SQLAlchemy UUID type sometimes behaves weirdly with Pydantic depending on config
    return SessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        title=session.title,
        created_at=session.created_at,
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for the current user."""
    sessions = await chat_service.get_user_sessions(db, current_user.id)
    return [
        SessionResponse(
            id=str(s.id),
            user_id=str(s.user_id),
            title=s.title,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat session by ID."""
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        title=session.title,
        created_at=session.created_at,
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await chat_service.delete_session(db, session)
    return


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a specific session."""
    # First verify the user owns the session
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await chat_service.get_session_messages(db, session_id)
    return [
        MessageResponse(
            id=str(m.id),
            session_id=str(m.session_id),
            raw_content=m.raw_content,
            polished_content=m.polished_content,
            created_at=m.created_at,
        )
        for m in messages
    ]
