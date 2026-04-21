from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 1. Create the engine (The physical connection)
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=True)

# 2. Create the session maker (The factory that produces workers)
SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 3. Dependency to get a DB session in our API routes
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()