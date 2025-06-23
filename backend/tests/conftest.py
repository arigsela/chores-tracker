import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import httpx

# Set testing flag before importing app
os.environ["TESTING"] = "true"

from backend.app.main import app
from backend.app.db.base import Base, get_db
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash
from backend.app.core.security.jwt import create_access_token
from backend.app.middleware.rate_limit import reset_limiter

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test."""
    async with test_engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session to use for testing
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Return a FastAPI test client with overridden dependencies."""
    # Reset rate limiter before each test
    reset_limiter()
    
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_parent_user(db_session):
    """Create a test parent user."""
    parent_user = User(
        email="parent@example.com",
        username="parent_user",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_parent=True
    )
    db_session.add(parent_user)
    await db_session.commit()
    await db_session.refresh(parent_user)
    return parent_user


@pytest_asyncio.fixture(scope="function")
async def test_child_user(db_session, test_parent_user):
    """Create a test child user."""
    child_user = User(
        email="child@example.com",
        username="child_user",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_parent=False,
        parent_id=test_parent_user.id
    )
    db_session.add(child_user)
    await db_session.commit()
    await db_session.refresh(child_user)
    return child_user


@pytest_asyncio.fixture(scope="function")
async def parent_token(test_parent_user):
    """Create a token for the parent user."""
    return create_access_token(subject=test_parent_user.id)


@pytest_asyncio.fixture(scope="function")
async def child_token(test_child_user):
    """Create a token for the child user."""
    return create_access_token(subject=test_child_user.id)


@pytest_asyncio.fixture(scope="function")
async def test_chore(db_session, test_parent_user, test_child_user):
    """Create a test chore with fixed reward."""
    chore = Chore(
        title="Clean room",
        description="Make sure to vacuum and dust",
        reward=5.00,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_disabled=False,
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture(scope="function")
async def test_range_chore(db_session, test_parent_user, test_child_user):
    """Create a test chore with range-based reward."""
    chore = Chore(
        title="Take out trash",
        description="Empty all trash cans and take to the curb",
        is_range_reward=True,
        min_reward=2.00,
        max_reward=4.00,
        cooldown_days=7,  # Weekly cooldown
        is_recurring=True,
        is_disabled=False,
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture(scope="function")
async def test_disabled_chore(db_session, test_parent_user, test_child_user):
    """Create a test disabled chore."""
    chore = Chore(
        title="Mow lawn",
        description="Mow the front and back lawn",
        reward=10.00,
        is_range_reward=False,
        cooldown_days=14,  # Bi-weekly cooldown
        is_recurring=True,
        is_disabled=True,
        assignee_id=test_child_user.id,
        creator_id=test_parent_user.id
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore 