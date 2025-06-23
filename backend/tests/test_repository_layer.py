"""
Test repository layer methods.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.repositories.chore import ChoreRepository
from backend.app.repositories.user import UserRepository
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash


class TestChoreRepositoryMethods:
    """Test ChoreRepository specific methods."""
    
    @pytest.mark.asyncio
    async def test_get_by_assignee(self, db_session: AsyncSession):
        """Test getting chores by assignee."""
        user_repo = UserRepository()
        chore_repo = ChoreRepository()
        
        # Create parent and child
        parent = User(
            username="parent_repo_test",
            email="parent_repo@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_repo_test",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Create chores for child
        chore1 = Chore(
            title="Chore 1",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        chore2 = Chore(
            title="Chore 2",
            description="Test",
            reward=10.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add_all([chore1, chore2])
        await db_session.commit()
        
        # Get chores by assignee
        chores = await chore_repo.get_by_assignee(db_session, assignee_id=child.id)
        assert len(chores) == 2
        assert all(c.assignee_id == child.id for c in chores)
    
    @pytest.mark.asyncio
    async def test_get_by_creator(self, db_session: AsyncSession):
        """Test getting chores by creator."""
        chore_repo = ChoreRepository()
        
        # Create parent
        parent = User(
            username="parent_creator_test",
            email="parent_creator@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        # Create chores by parent
        chore1 = Chore(
            title="Created Chore 1",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=None,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        chore2 = Chore(
            title="Created Chore 2",
            description="Test",
            reward=10.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=None,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add_all([chore1, chore2])
        await db_session.commit()
        
        # Get chores by creator
        chores = await chore_repo.get_by_creator(db_session, creator_id=parent.id)
        assert len(chores) == 2
        assert all(c.creator_id == parent.id for c in chores)
    
    @pytest.mark.asyncio
    async def test_get_pending_approval(self, db_session: AsyncSession):
        """Test getting chores pending approval."""
        chore_repo = ChoreRepository()
        
        # Create parent and child
        parent = User(
            username="parent_pending_test",
            email="parent_pending@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_pending_test",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Create various chores
        completed_pending = Chore(
            title="Pending Approval",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=True,
            is_approved=False,
            is_disabled=False
        )
        not_completed = Chore(
            title="Not Completed",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        already_approved = Chore(
            title="Already Approved",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=True,
            is_approved=True,
            is_disabled=False
        )
        db_session.add_all([completed_pending, not_completed, already_approved])
        await db_session.commit()
        
        # Get pending approval chores
        pending = await chore_repo.get_pending_approval(db_session, creator_id=parent.id)
        assert len(pending) == 1
        assert pending[0].title == "Pending Approval"
        assert pending[0].is_completed is True
        assert pending[0].is_approved is False
    
    @pytest.mark.asyncio
    async def test_get_completed_by_child(self, db_session: AsyncSession):
        """Test getting completed chores by child."""
        chore_repo = ChoreRepository()
        
        # Create parent and child
        parent = User(
            username="parent_comp_child",
            email="parent_comp_ch@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        child = User(
            username="child_comp_repo",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add(child)
        await db_session.commit()
        
        # Create chores
        completed = Chore(
            title="Completed Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=True,
            is_approved=True,
            is_disabled=False,
            completion_date=datetime.utcnow()
        )
        not_completed = Chore(
            title="Not Completed",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add_all([completed, not_completed])
        await db_session.commit()
        
        # Get completed chores
        completed_chores = await chore_repo.get_completed_by_child(db_session, child_id=child.id)
        assert len(completed_chores) == 1
        assert completed_chores[0].title == "Completed Chore"
        assert completed_chores[0].is_completed is True
    
    @pytest.mark.asyncio
    async def test_disable_chore(self, db_session: AsyncSession):
        """Test disabling a chore."""
        chore_repo = ChoreRepository()
        
        # Create parent
        parent = User(
            username="parent_disable_repo",
            email="parent_dis_repo@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        # Create chore
        chore = Chore(
            title="To Disable",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=None,
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add(chore)
        await db_session.commit()
        
        # Disable it
        disabled = await chore_repo.disable_chore(db_session, chore_id=chore.id)
        assert disabled.is_disabled is True
        
        # Verify in DB
        result = await db_session.execute(
            select(Chore).where(Chore.id == chore.id)
        )
        db_chore = result.scalar_one()
        assert db_chore.is_disabled is True


class TestUserRepositoryMethods:
    """Test UserRepository specific methods."""
    
    @pytest.mark.asyncio
    async def test_get_by_username(self, db_session: AsyncSession):
        """Test getting user by username."""
        user_repo = UserRepository()
        
        # Create user
        user = User(
            username="unique_username",
            email="unique@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Get by username
        found_user = await user_repo.get_by_username(db_session, username="unique_username")
        assert found_user is not None
        assert found_user.username == "unique_username"
        assert found_user.email == "unique@test.com"
        
        # Try non-existent username
        not_found = await user_repo.get_by_username(db_session, username="does_not_exist")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession):
        """Test getting user by email."""
        user_repo = UserRepository()
        
        # Create user
        user = User(
            username="email_test_user",
            email="test_email@example.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Get by email
        found_user = await user_repo.get_by_email(db_session, email="test_email@example.com")
        assert found_user is not None
        assert found_user.email == "test_email@example.com"
        assert found_user.username == "email_test_user"
        
        # Try non-existent email
        not_found = await user_repo.get_by_email(db_session, email="not@found.com")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_get_children(self, db_session: AsyncSession):
        """Test getting children by parent."""
        user_repo = UserRepository()
        
        # Create parent
        parent = User(
            username="parent_eager",
            email="parent_eager@test.com",
            hashed_password=get_password_hash("password"),
            is_parent=True,
            is_active=True
        )
        db_session.add(parent)
        await db_session.commit()
        
        # Create children
        child1 = User(
            username="child1_eager",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        child2 = User(
            username="child2_eager",
            hashed_password=get_password_hash("password"),
            is_parent=False,
            is_active=True,
            parent_id=parent.id
        )
        db_session.add_all([child1, child2])
        await db_session.commit()
        
        # Get children
        children = await user_repo.get_children(db_session, parent_id=parent.id)
        assert len(children) == 2
        assert all(c.parent_id == parent.id for c in children)
        assert {c.username for c in children} == {"child1_eager", "child2_eager"}
    
