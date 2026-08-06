"""
conftest.py — Shared test fixtures for all backend tests.

Uses an in-memory SQLite database so tests run without PostgreSQL.
Each test function gets a fresh database to ensure isolation.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.db.session import get_db
from app.main import app


# ── In-memory SQLite engine for testing ───────────────────────────────────────
# StaticPool + check_same_thread=False ensures all async tasks share
# the same in-memory database within a single test.

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Event loop fixture (required by pytest-asyncio) ──────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Database setup/teardown per test ─────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Override the get_db dependency ───────────────────────────────────────────

async def override_get_db():
    """Yield a test database session instead of the real PostgreSQL one."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


# ── Async HTTP client fixture ────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """
    Provide an httpx.AsyncClient wired to the FastAPI app.
    This lets us call endpoints like: response = await client.post("/api/v1/auth/register", ...)
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ── Helper: register + login and return tokens ──────────────────────────────

@pytest_asyncio.fixture
async def auth_tokens(client: AsyncClient):
    """Register a test user and log in, returning the token pair."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
        },
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123!",
        },
    )
    return response.json()
