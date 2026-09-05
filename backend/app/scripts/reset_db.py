import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import engine
from app.models.base import Base

# Import all models so they are registered with Base
from app.models.user import User
from app.models.session import ChatSession
from app.models.message import Message
from app.models.feedback import Feedback
from app.models.preference import UserPreference
from app.models.usage_log import UsageLog
from app.models.prompt_history import PromptHistory
from sqlalchemy import text

async def reset_db():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        # Drop all tables known to the models
        await conn.run_sync(Base.metadata.drop_all)
        # Drop alembic_version explicitly just in case
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        
        print("Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database reset complete!")

if __name__ == "__main__":
    asyncio.run(reset_db())
