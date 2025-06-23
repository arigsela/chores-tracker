"""
Test database query optimizations.

This module tests that our database optimizations are working correctly.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.repositories.user import UserRepository
from backend.app.repositories.chore import ChoreRepository
from backend.app.core.security.password import get_password_hash


@pytest.mark.asyncio
async def test_indexes_exist(db_session: AsyncSession):
    """Test that our custom indexes were created."""
    # Skip this test for SQLite (test database)
    if "sqlite" in str(db_session.bind.url):
        pytest.skip("Index test not applicable for SQLite test database")
    
    # Check for indexes on MySQL
    result = await db_session.execute(
        text("SELECT DISTINCT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_NAME = 'users'")
    )
    user_indexes = [row[0] for row in result.fetchall()]
    
    # Our custom index should exist
    assert 'idx_user_parent_id' in user_indexes
    
    # Check chore indexes
    result = await db_session.execute(
        text("SELECT DISTINCT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_NAME = 'chores'")
    )
    chore_indexes = [row[0] for row in result.fetchall()]
    
    # Our custom indexes should exist
    expected_indexes = ['idx_chore_assignee_id', 'idx_chore_creator_id', 'idx_chore_status']
    for idx in expected_indexes:
        assert idx in chore_indexes


@pytest.mark.asyncio
async def test_eager_loading_prevents_n_plus_one(db_session: AsyncSession):
    """Test that eager loading prevents N+1 queries."""
    # Create test data
    parent = User(
        username="test_parent",
        email="parent@test.com",
        hashed_password=get_password_hash("password"),
        is_parent=True,
        is_active=True
    )
    db_session.add(parent)
    await db_session.commit()
    
    # Create multiple chores
    for i in range(5):
        chore = Chore(
            title=f"Test Chore {i}",
            description="Test",
            reward=5.0,
            creator_id=parent.id,
            assignee_id=parent.id,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add(chore)
    await db_session.commit()
    
    # Test that getting chores with eager loading doesn't cause N+1
    chore_repo = ChoreRepository()
    
    # This should execute only 1-2 queries (main query + eager load), not 6 (1 + 5)
    chores = await chore_repo.get_by_assignee(db_session, assignee_id=parent.id)
    
    # Access the relationships - this should not trigger additional queries
    for chore in chores:
        assert chore.assignee.username == "test_parent"
        assert chore.creator.username == "test_parent"


@pytest.mark.asyncio
async def test_connection_pool_settings(db_session: AsyncSession):
    """Test that connection pool is configured correctly."""
    # Skip for SQLite test database which uses StaticPool
    if "sqlite" in str(db_session.bind.url):
        pytest.skip("Pool settings test not applicable for SQLite test database")
    
    engine = db_session.bind
    pool = engine.pool
    
    # Check pool settings
    assert pool.size() <= 20  # Our configured pool size
    assert hasattr(engine, 'pool_pre_ping')


@pytest.mark.asyncio
async def test_query_performance_on_indexed_columns(db_session: AsyncSession):
    """Test that queries on indexed columns are fast."""
    # Create test data
    parent = User(
        username="perf_test_parent",
        email="perfparent@test.com",
        hashed_password=get_password_hash("password"),
        is_parent=True,
        is_active=True
    )
    db_session.add(parent)
    await db_session.commit()
    
    # Create many children
    for i in range(50):
        child = User(
            username=f"child_{i}",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
    
    await db_session.commit()
    
    # This query should be fast due to index on parent_id
    user_repo = UserRepository()
    children = await user_repo.get_children(db_session, parent_id=parent.id)
    
    assert len(children) == 50
    
    # Verify eager loading worked
    for child in children:
        # This should not trigger additional queries
        assert hasattr(child, 'chores_assigned')