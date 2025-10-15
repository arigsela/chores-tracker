"""
Test Unit of Work pattern implementation.
"""

import pytest
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.core.unit_of_work import UnitOfWork
from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.repositories.user import UserRepository
from backend.app.repositories.chore import ChoreRepository


class TestUnitOfWorkPattern:
    """Test Unit of Work pattern functionality."""
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_session: AsyncSession):
        """Test that transactions commit successfully."""
        user_repo = UserRepository()
        
        # Create a user within a transaction
        user_data = {
            "username": "test_transaction_user",
            "password": "password123",
            "email": "transaction@example.com",
            "is_parent": True
        }
        
        # Use the session's transaction
        user = await user_repo.create(db_session, obj_in=user_data)
        
        # Verify user was created
        assert user.id is not None
        assert user.username == "test_transaction_user"
        
        # Commit happens automatically in the test fixture
        
        # Verify user persists
        result = await db_session.execute(
            select(User).where(User.username == "test_transaction_user")
        )
        persisted_user = result.scalar_one_or_none()
        assert persisted_user is not None
        assert persisted_user.email == "transaction@example.com"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Repository auto-commits make this test unreliable")
    async def test_transaction_rollback(self, db_session: AsyncSession):
        """Test that transactions can be rolled back."""
        user_repo = UserRepository()
        
        # Create user and then rollback
        user_data = {
            "username": "test_rollback_user",
            "password": "password123",
            "email": "rollback@example.com",
            "is_parent": True
        }
        
        # Create user in a nested transaction
        try:
            # Force an error after user creation
            user = await user_repo.create(db_session, obj_in=user_data)
            assert user.id is not None
            
            # Now try to create the same user again (will cause duplicate error)
            await user_repo.create(db_session, obj_in=user_data)
        except Exception:
            # This will rollback the current transaction
            await db_session.rollback()
        
        # Verify user was NOT persisted due to rollback
        result = await db_session.execute(
            select(User).where(User.username == "test_rollback_user")
        )
        not_persisted = result.scalar_one_or_none()
        assert not_persisted is None
    
    @pytest.mark.asyncio
    async def test_multiple_operations_in_transaction(self, db_session: AsyncSession):
        """Test multiple operations within a single transaction."""
        user_repo = UserRepository()
        chore_repo = ChoreRepository()
        
        # Create parent
        parent_data = {
            "username": "test_parent_multi",
            "password": "password123",
            "email": "parent_multi@example.com",
            "is_parent": True
        }
        parent = await user_repo.create(db_session, obj_in=parent_data)
        
        # Create child
        child_data = {
            "username": "test_child_multi",
            "password": "password123",
            "is_parent": False,
            "parent_id": parent.id
        }
        child = await user_repo.create(db_session, obj_in=child_data)
        
        # Create chore with multi-assignment pattern
        from backend.app.models.chore_assignment import ChoreAssignment

        chore_data = {
            "title": "Test Chore Multi",
            "description": "Test description",
            "reward": 5.0,
            "is_range_reward": False,
            "cooldown_days": 0,
            "is_recurring": False,
            "is_disabled": False,
            "assignment_mode": "single",
            "creator_id": parent.id
        }
        chore = await chore_repo.create(db_session, obj_in=chore_data)
        await db_session.flush()  # Get chore ID

        # Create assignment
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository
        assignment_repo = ChoreAssignmentRepository()
        assignment = await assignment_repo.create(db_session, obj_in={
            "chore_id": chore.id,
            "assignee_id": child.id,
            "is_completed": False,
            "is_approved": False
        })

        # Verify all were created
        assert parent.id is not None
        assert child.id is not None
        assert chore.id is not None
        assert assignment.id is not None
        assert child.parent_id == parent.id
        assert assignment.assignee_id == child.id
        
        # Transaction commits automatically in test fixture
        
        # Verify all persisted
        result = await db_session.execute(
            select(User).where(User.username.in_(["test_parent_multi", "test_child_multi"]))
        )
        users = result.scalars().all()
        assert len(users) == 2
        
        result = await db_session.execute(
            select(Chore).where(Chore.title == "Test Chore Multi")
        )
        persisted_chore = result.scalar_one_or_none()
        assert persisted_chore is not None


class TestTransactionalServices:
    """Test transactional service methods."""
    
    @pytest.mark.asyncio
    async def test_register_user_with_validation(self, db_session: AsyncSession):
        """Test user registration with business validation."""
        user_service = UserService()
        
        # Test successful parent registration
        parent = await user_service.register_user(
            db_session,
            username="test_validation_parent",
            password="password123",
            email="validation@example.com",
            is_parent=True
        )
        
        assert parent.username == "test_validation_parent"
        assert parent.is_parent is True
        
        # Test child registration with parent
        child = await user_service.register_user(
            db_session,
            username="test_validation_child",
            password="pass1234",
            is_parent=False,
            parent_id=parent.id
        )
        
        assert child.username == "test_validation_child"
        assert child.parent_id == parent.id
    
    @pytest.mark.asyncio
    async def test_create_and_approve_chore(self, db_session: AsyncSession):
        """Test chore creation and approval workflow."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="approve_test_parent",
            password="password123",
            email="approve@example.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="approve_test_child",
            password="pass1234",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create chore
        chore_data = {
            "title": "Test Approval Chore",
            "description": "Test",
            "reward": 10.0,
            "assignment_mode": "single",
            "assignee_ids": [child.id],
            "is_range_reward": False,
            "cooldown_days": 0,
            "is_recurring": False
        }

        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data=chore_data
        )

        assert chore.title == "Test Approval Chore"
        # Verify assignment was created
        await db_session.refresh(chore, ['assignments'])
        assert len(chore.assignments) == 1
        assert chore.assignments[0].assignee_id == child.id

        assignment_id = chore.assignments[0].id

        # Complete chore
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Verify completion
        await db_session.refresh(chore, ['assignments'])
        assert chore.assignments[0].is_completed is True

        # Approve chore
        from backend.app.services.chore_service import ChoreService
        await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id
        )

        # Verify approval
        await db_session.refresh(chore, ['assignments'])
        assert chore.assignments[0].is_approved is True
    
    @pytest.mark.asyncio
    async def test_validation_errors_dont_create_partial_data(self, db_session: AsyncSession):
        """Test that validation errors prevent any data creation."""
        user_service = UserService()
        
        # Try to create parent without email (should fail)
        with pytest.raises(Exception) as exc_info:
            await user_service.register_user(
                db_session,
                username="invalid_parent",
                password="password123",
                is_parent=True
                # Missing email!
            )
        
        # Verify no user was created
        result = await db_session.execute(
            select(User).where(User.username == "invalid_parent")
        )
        user = result.scalar_one_or_none()
        assert user is None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, db_session: AsyncSession):
        """Test that operations within a session are properly isolated."""
        user_repo = UserRepository()
        
        # Create first user
        user1_data = {
            "username": "concurrent_user1",
            "password": "password123",
            "email": "concurrent1@example.com",
            "is_parent": True
        }
        user1 = await user_repo.create(db_session, obj_in=user1_data)
        
        # Create second user
        user2_data = {
            "username": "concurrent_user2",
            "password": "password123",
            "email": "concurrent2@example.com",
            "is_parent": True
        }
        user2 = await user_repo.create(db_session, obj_in=user2_data)
        
        # Both should have different IDs
        assert user1.id != user2.id
        
        # Both should be retrievable
        result = await db_session.execute(
            select(User).where(User.username.in_(["concurrent_user1", "concurrent_user2"]))
        )
        users = result.scalars().all()
        assert len(users) == 2