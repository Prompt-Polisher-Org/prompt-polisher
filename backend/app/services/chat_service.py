"""
services/chat_service.py — Business logic for chat sessions and messages.
"""
import uuid
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import ChatSession
from app.models.message import Message

async def create_session(db: AsyncSession, user_id: uuid.UUID, title: str) -> ChatSession:
    session = ChatSession(id=uuid.uuid4(), user_id=user_id, title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def get_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> Sequence[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
    )
    return result.scalars().all()

async def get_session(db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.commit()

async def get_session_messages(db: AsyncSession, session_id: uuid.UUID) -> Sequence[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()
