from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 1. Create the engine with production-grade connection pool settings
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,  # Set True only for debugging SQL queries
    # ── Connection Pool Configuration ──────────────────────────────────
    pool_size=10,          # Maintain 10 persistent connections in the pool
    max_overflow=20,       # Allow up to 20 additional connections under load
    pool_timeout=30,       # Wait up to 30s for a connection before raising error
    pool_recycle=1800,     # Recycle connections every 30 min (prevents stale conn)
    pool_pre_ping=True,    # Verify connection is alive before using it
)

# 2. Create the session maker (The factory that produces workers)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 3. Dependency to get a DB session in our API routes
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()