"""
seed_data.py — Populate the database with sample data for development.

Task: Week 3-4 / Database & Migrations (task.md line 178)
  [ ] Create seed data script for development

Usage:
    cd backend
    python -m scripts.seed_data

Creates:
  - 3 demo users (alice, bob, charlie)
  - Preferences for each user
  - 2 chat sessions with sample messages
"""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.base import Base
from app.models.user import User
from app.models.preference import UserPreference
from app.models.session import ChatSession
from app.models.message import Message


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # ── Users ────────────────────────────────────────────────────────
        alice_id = uuid.uuid4()
        bob_id = uuid.uuid4()
        charlie_id = uuid.uuid4()

        users = [
            User(
                id=alice_id,
                email="alice@example.com",
                full_name="Alice Smith",
                hashed_password=hash_password("Password123!"),
                is_active=True,
            ),
            User(
                id=bob_id,
                email="bob@example.com",
                full_name="Bob Johnson",
                hashed_password=hash_password("Password123!"),
                is_active=True,
            ),
            User(
                id=charlie_id,
                email="charlie@example.com",
                full_name="Charlie Davis",
                hashed_password=hash_password("Password123!"),
                is_active=True,
            ),
        ]
        db.add_all(users)
        await db.flush()

        # ── Preferences ─────────────────────────────────────────────────
        preferences = [
            UserPreference(
                id=uuid.uuid4(),
                user_id=alice_id,
                tone="professional",
                verbosity="detailed",
                target_model="GPT-4",
                domain="marketing",
                custom_instructions="Always include a call-to-action.",
            ),
            UserPreference(
                id=uuid.uuid4(),
                user_id=bob_id,
                tone="casual",
                verbosity="concise",
                target_model="Claude",
                domain="coding",
                custom_instructions="Use Python examples where possible.",
            ),
            UserPreference(
                id=uuid.uuid4(),
                user_id=charlie_id,
                tone="academic",
                verbosity="balanced",
                target_model="Gemini",
                domain="writing",
                custom_instructions=None,
            ),
        ]
        db.add_all(preferences)
        await db.flush()

        # ── Chat Sessions & Messages ────────────────────────────────────
        session1_id = uuid.uuid4()
        session2_id = uuid.uuid4()

        sessions = [
            ChatSession(id=session1_id, user_id=alice_id, title="Marketing Email Draft"),
            ChatSession(id=session2_id, user_id=bob_id, title="Python Code Review"),
        ]
        db.add_all(sessions)
        await db.flush()

        messages = [
            Message(
                id=uuid.uuid4(),
                session_id=session1_id,
                raw_content="Write me a marketing email for our new product launch",
                polished_content="Craft a compelling marketing email announcing our latest product launch. Include a strong subject line, highlight key benefits, and end with a clear call-to-action.",
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session1_id,
                raw_content="Make it more urgent",
                polished_content="Revise the marketing email to convey urgency. Use time-sensitive language, emphasize limited availability, and create a sense of FOMO (fear of missing out) while maintaining professionalism.",
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session2_id,
                raw_content="Review this python function for bugs",
                polished_content="Perform a thorough code review of the following Python function. Identify potential bugs, suggest performance improvements, and recommend best practices for readability and maintainability.",
            ),
        ]
        db.add_all(messages)

        await db.commit()
        print("✅ Seed data created successfully!")
        print(f"   - 3 users: alice@example.com, bob@example.com, charlie@example.com")
        print(f"   - Password for all: Password123!")
        print(f"   - 3 user preferences")
        print(f"   - 2 chat sessions with 3 messages")


if __name__ == "__main__":
    asyncio.run(seed())
