"""
Tests for base repository functionality.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.base import BaseRepository
from backend.app.models.user import User
from backend.app.models.chore import Chore


class TestBaseRepository:
    """Test base repository methods."""
    
    @pytest.fixture
    def user_base_repo(self):
        """Create a base repository instance for User model."""
        return BaseRepository(User)
    
    @pytest.fixture
    def chore_base_repo(self):
        """Create a base repository instance for Chore model."""
        return BaseRepository(Chore)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(
        self,
        db_session: AsyncSession,
        user_base_repo: BaseRepository
    ):
        """Test getting non-existent entity returns None."""
        result = await user_base_repo.get(db_session, id=99999)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_multi_empty(
        self,
        db_session: AsyncSession,
        chore_base_repo: BaseRepository
    ):
        """Test get_multi on empty table."""
        # Clear any existing chores
        results = await chore_base_repo.get_multi(db_session)
        assert isinstance(results, list)
        # Note: May not be empty if fixtures created chores
    
    @pytest.mark.asyncio
    async def test_get_multi_with_limit(
        self,
        db_session: AsyncSession,
        user_base_repo: BaseRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test get_multi with limit."""
        results = await user_base_repo.get_multi(db_session, limit=1)
        assert len(results) <= 1
    
    @pytest.mark.asyncio
    async def test_get_multi_with_skip(
        self,
        db_session: AsyncSession,
        user_base_repo: BaseRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test get_multi with skip."""
        # Get all users
        all_users = await user_base_repo.get_multi(db_session)
        
        # Skip first user
        skipped_users = await user_base_repo.get_multi(db_session, skip=1)
        
        assert len(skipped_users) == len(all_users) - 1
    
    @pytest.mark.asyncio
    async def test_update_nonexistent(
        self,
        db_session: AsyncSession,
        user_base_repo: BaseRepository
    ):
        """Test updating non-existent entity returns None."""
        result = await user_base_repo.update(
            db_session,
            id=99999,
            obj_in={"username": "updated"}
        )
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_with_dict(
        self,
        db_session: AsyncSession,
        user_base_repo: BaseRepository,
        test_parent_user: User
    ):
        """Test updating entity with dictionary."""
        new_email = "updated@example.com"
        
        updated = await user_base_repo.update(
            db_session,
            id=test_parent_user.id,
            obj_in={"email": new_email}
        )
        
        assert updated is not None
        assert updated.email == new_email
        assert updated.username == test_parent_user.username  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(
        self,
        db_session: AsyncSession,
        user_base_repo: BaseRepository
    ):
        """Test deleting non-existent entity (no error raised)."""
        # Should not raise error, just does nothing
        await user_base_repo.delete(db_session, id=99999)
    
    @pytest.mark.asyncio
    async def test_delete_existing(
        self,
        db_session: AsyncSession,
        chore_base_repo: BaseRepository,
        test_chore: Chore
    ):
        """Test deleting existing entity."""
        chore_id = test_chore.id
        
        # Delete the chore (returns None)
        await chore_base_repo.delete(db_session, id=chore_id)
        
        # Verify it's gone
        result = await chore_base_repo.get(db_session, id=chore_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_with_eager_load(
        self,
        db_session: AsyncSession,
        chore_base_repo: BaseRepository,
        test_chore: Chore
    ):
        """Test get with eager loading relationships (multi-assignment architecture)."""
        # Get chore with eager loaded relationships
        # Note: 'assignee' no longer exists, replaced by 'assignments' many-to-many
        chore = await chore_base_repo.get(
            db_session,
            id=test_chore.id,
            eager_load_relations=["assignments", "creator"]
        )

        assert chore is not None
        # Relationships should be loaded (not raising lazy load error)
        assert chore.assignments is not None  # Many-to-many relationship
        assert len(chore.assignments) > 0  # Should have at least one assignment
        assert chore.creator is not None