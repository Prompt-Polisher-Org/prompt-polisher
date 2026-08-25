"""
worker_tasks/embed_tasks.py — Celery tasks for background embedding into Qdrant.

Task: Week 7-8 / Ingestion Pipeline (task.md lines 388-390)
  [x] Auto-embed messages after creation (Celery task)
  [x] Batch embedding for historical data backfill
"""
import logging
import uuid

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.worker_tasks.embed_tasks.embed_message",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def embed_message(
    self,
    message_id: str,
    session_id: str,
    user_id: str,
    content: str,
) -> dict:
    """
    Celery task: embed a single chat message and upsert it into Qdrant.

    This is dispatched immediately after a message is saved to Postgres.
    Running it in a background task means the HTTP response is sent to the
    user right away while the vector is computed asynchronously.

    Args:
        message_id: UUID string of the Message row.
        session_id: UUID string of the parent ChatSession.
        user_id:    UUID string of the owner user.
        content:    The message text to embed.
    """
    try:
        # Deferred imports — keeps Celery startup fast and prevents circular imports
        from app.services.embedding_service import embedding_service
        from app.services.qdrant_service import qdrant_service

        vector = embedding_service.embed_text(content)
        qdrant_service.upsert_message(
            message_id=message_id,
            vector=vector,
            payload={
                "user_id": user_id,
                "session_id": session_id,
                "content": content,
                "message_id": message_id,
            },
        )
        logger.info(f"Embedded message {message_id} for user {user_id}")
        return {"status": "ok", "message_id": message_id}

    except Exception as exc:
        logger.error(f"Failed to embed message {message_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.worker_tasks.embed_tasks.backfill_user_embeddings",
    bind=True,
)
def backfill_user_embeddings(self, user_id: str) -> dict:
    """
    Celery task: batch-embed all historical messages for a user.

    Used for backfilling data when RAG is first enabled or when a user's
    history has not been embedded yet. Runs as a one-off admin task.

    Strategy:
    1. Load all messages for the user from Postgres via synchronous SQLAlchemy.
    2. Embed them in a single batch call (64 texts per GPU forward pass).
    3. Upsert all vectors into the Qdrant chat_history collection.
    """
    from app.services.embedding_service import embedding_service
    from app.services.qdrant_service import qdrant_service
    from app.core.config import settings

    # Build a synchronous DB URL for the Celery worker context
    # (no asyncio event loop is available inside a Celery task by default)
    sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    try:
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import Session
        from app.models.message import Message
        from app.models.session import ChatSession
    except ImportError as e:
        logger.warning(f"Required import unavailable in backfill task: {e}")
        return {"status": "skipped", "reason": str(e)}

    try:
        engine = create_engine(sync_db_url)
        with Session(engine) as db:
            # Step 1: Get all chat sessions belonging to this user
            user_sessions = db.execute(
                select(ChatSession).where(
                    ChatSession.user_id == uuid.UUID(user_id)
                )
            ).scalars().all()

            if not user_sessions:
                logger.info(f"No sessions found for user {user_id}; nothing to backfill.")
                return {"status": "ok", "embedded": 0}

            session_ids = [s.id for s in user_sessions]

            # Step 2: Load all messages across those sessions
            messages = db.execute(
                select(Message).where(Message.session_id.in_(session_ids))
            ).scalars().all()

    except Exception as exc:
        logger.error(f"DB error during backfill for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=30, max_retries=2)

    if not messages:
        logger.info(f"No messages found for user {user_id}; nothing to backfill.")
        return {"status": "ok", "embedded": 0}

    # Step 3: Build text strings for batch embedding
    texts = []
    meta = []
    for msg in messages:
        # Combine raw and polished content into a single searchable string
        parts = [p for p in [msg.raw_content, msg.polished_content] if p]
        content = " ".join(parts)
        texts.append(content)
        meta.append({
            "message_id": str(msg.id),
            "session_id": str(msg.session_id),
            "user_id": user_id,
            "content": content,
        })

    # Step 4: Batch embed — much faster than one-at-a-time
    vectors = embedding_service.embed_batch(texts)

    # Step 5: Upsert each vector into Qdrant
    for vec, m in zip(vectors, meta):
        try:
            qdrant_service.upsert_message(
                message_id=m["message_id"],
                vector=vec,
                payload=m,
            )
        except Exception as e:
            logger.warning(f"Failed to upsert message {m['message_id']}: {e}")

    logger.info(f"Backfilled {len(texts)} message embeddings for user {user_id}.")
    return {"status": "ok", "embedded": len(texts)}
