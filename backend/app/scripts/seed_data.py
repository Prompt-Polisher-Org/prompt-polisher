import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.session import ChatSession
from app.models.message import Message
from app.models.feedback import Feedback

async def seed():
    print("Seeding mock feedback data...")
    async with SessionLocal() as db:
        # 1. Create a dummy user
        user = User(
            email="test_dpo@example.com",
            hashed_password="hashedpassword123",
            full_name="DPO Tester",
            is_active=True
        )
        db.add(user)
        await db.flush()
        
        # 2. Create a chat session
        session = ChatSession(
            user_id=user.id,
            title="DPO Test Session"
        )
        db.add(session)
        await db.flush()
        
        # 3. Create mock messages and feedback
        
        # Scenario A: User likes the output
        msg1 = Message(
            session_id=session.id,
            raw_content="write a python script to parse json",
            polished_content="Write a robust Python script to parse a JSON file, handle common errors like FileNotFoundError and json.JSONDecodeError, and extract specific nested keys.",
        )
        db.add(msg1)
        await db.flush()
        
        fb1 = Feedback(
            message_id=msg1.id,
            user_id=user.id,
            rating=1,  # Thumbs up
            comment="Great prompt!"
        )
        db.add(fb1)
        
        # Scenario B: User dislikes the output
        msg2 = Message(
            session_id=session.id,
            raw_content="write a python script to parse json",
            polished_content="Code a python script for json.",
        )
        db.add(msg2)
        await db.flush()
        
        fb2 = Feedback(
            message_id=msg2.id,
            user_id=user.id,
            rating=-1, # Thumbs down
            comment="Too short, not helpful"
        )
        db.add(fb2)
        
        # Scenario C: User only likes the output (no rejected pair)
        msg3 = Message(
            session_id=session.id,
            raw_content="explain quantum physics to a 5 year old",
            polished_content="Explain the core concepts of quantum physics using simple analogies suitable for a 5-year-old child, avoiding complex jargon.",
        )
        db.add(msg3)
        await db.flush()
        
        fb3 = Feedback(
            message_id=msg3.id,
            user_id=user.id,
            rating=1,
        )
        db.add(fb3)
        
        await db.commit()
        print("Successfully seeded database with mock DPO feedback data!")

if __name__ == "__main__":
    asyncio.run(seed())
