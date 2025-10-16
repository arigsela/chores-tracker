"""
Test service methods that use Unit of Work pattern.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from backend.app.core.unit_of_work import UnitOfWork
from backend.app.services.chore_service import ChoreService
from backend.app.services.user_service import UserService
from backend.app.models.user import User
from backend.app.models.chore import Chore


@pytest.fixture
def test_uow_factory(db_session):
    """Create a factory for UnitOfWork that uses the test session."""
    # Return a callable that returns the session directly (not async)
    return lambda: db_session


class TestUnitOfWorkServiceMethods:
    """Test service methods that use UnitOfWork for transactional operations."""
    
    @pytest.mark.asyncio
    async def test_bulk_assign_chores_success(self, db_session: AsyncSession, test_uow_factory):
        """Test successful bulk assignment of chores."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="bulk_parent",
            password="password123",
            email="bulk@example.com",
            is_parent=True
        )
        
        # Create two children
        child1 = await user_service.register_user(
            db_session,
            username="bulk_child1",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        child2 = await user_service.register_user(
            db_session,
            username="bulk_child2",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Prepare bulk assignments
        assignments = [
            {
                "title": "Clean Room",
                "description": "Clean your bedroom",
                "assignee_id": child1.id,
                "reward": 5.0,
                "cooldown_days": 7,
                "is_recurring": True
            },
            {
                "title": "Do Homework",
                "description": "Complete all homework",
                "assignee_id": child2.id,
                "reward": 10.0,
                "cooldown_days": 1,
                "is_recurring": True
            },
            {
                "title": "Walk Dog",
                "description": "Take the dog for a walk",
                "assignee_id": child1.id,
                "reward": 3.0,
                "is_range_reward": True,
                "min_reward": 2.0,
                "max_reward": 5.0
            }
        ]
        
        # Perform bulk assignment
        async with UnitOfWork(session_factory=test_uow_factory) as uow:
            created_chores = await chore_service.bulk_assign_chores(
                uow,
                creator_id=parent.id,
                assignments=assignments
            )
            await uow.commit()
        
        # Verify all chores were created
        assert len(created_chores) == 3

        # Verify chore details
        assert created_chores[0].title == "Clean Room"
        assert created_chores[0].assignment_mode == "single"
        assert created_chores[0].is_recurring is True

        assert created_chores[1].title == "Do Homework"
        assert created_chores[1].assignment_mode == "single"

        assert created_chores[2].title == "Walk Dog"
        assert created_chores[2].is_range_reward is True
        assert created_chores[2].min_reward == 2.0
        assert created_chores[2].max_reward == 5.0

        # Verify assignments were created
        # Need to check the database for ChoreAssignment records
        from backend.app.models.chore_assignment import ChoreAssignment
        from sqlalchemy import select

        # Check assignment for chore 1 (child1)
        stmt = select(ChoreAssignment).where(ChoreAssignment.chore_id == created_chores[0].id)
        result = await db_session.execute(stmt)
        assignment = result.scalars().first()
        assert assignment is not None
        assert assignment.assignee_id == child1.id
        assert assignment.is_completed is False
        assert assignment.is_approved is False

        # Check assignment for chore 2 (child2)
        stmt = select(ChoreAssignment).where(ChoreAssignment.chore_id == created_chores[1].id)
        result = await db_session.execute(stmt)
        assignment = result.scalars().first()
        assert assignment is not None
        assert assignment.assignee_id == child2.id

        # Check assignment for chore 3 (child1)
        stmt = select(ChoreAssignment).where(ChoreAssignment.chore_id == created_chores[2].id)
        result = await db_session.execute(stmt)
        assignment = result.scalars().first()
        assert assignment is not None
        assert assignment.assignee_id == child1.id
    
    @pytest.mark.skip(reason="UnitOfWork rollback doesn't work properly with shared test session")
    @pytest.mark.asyncio
    async def test_bulk_assign_chores_rollback_on_error(self, db_session: AsyncSession, test_uow_factory):
        """Test that bulk assignment rolls back on error.
        
        Note: This test is skipped because the UnitOfWork pattern expects to manage
        its own session, but in tests we share the same session which prevents
        proper rollback isolation.
        """
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="bulk_error_parent",
            password="password123",
            email="bulk_error@example.com",
            is_parent=True
        )
        parent_id = parent.id  # Store ID before potential session closure
        
        # Create one child
        child = await user_service.register_user(
            db_session,
            username="bulk_error_child",
            password="password123",
            is_parent=False,
            parent_id=parent_id
        )
        child_id = child.id  # Store ID before potential session closure
        
        # Commit the users so they persist
        await db_session.commit()
        
        # Count chores before the operation
        parent = await user_service.get(db_session, id=parent_id)
        chores_before = await chore_service.get_chores_for_user(db_session, user=parent)
        initial_count = len(chores_before)
        
        # Prepare assignments with one invalid (non-existent child)
        assignments = [
            {
                "title": "Valid Chore",
                "description": "This should not be created",
                "assignee_id": child_id,
                "reward": 5.0
            },
            {
                "title": "Invalid Chore", 
                "description": "This will cause an error",
                "assignee_id": 99999,  # Non-existent child
                "reward": 10.0
            }
        ]
        
        # Try bulk assignment - should fail
        with pytest.raises(Exception):
            async with UnitOfWork(session_factory=test_uow_factory) as uow:
                await chore_service.bulk_assign_chores(
                    uow,
                    creator_id=parent_id,
                    assignments=assignments
                )
                await uow.commit()
        
        # Verify no new chores were created (transaction rolled back)
        # Re-fetch the parent to avoid detached instance error
        await db_session.rollback()  # Ensure we see fresh data
        parent = await user_service.get(db_session, id=parent_id)
        chores_after = await chore_service.get_chores_for_user(db_session, user=parent)
        assert len(chores_after) == initial_count  # No new chores should exist
    
    @pytest.mark.asyncio
    async def test_approve_chore_with_next_instance(self, db_session: AsyncSession, test_uow_factory):
        """Test approving a recurring chore creates next instance."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="approve_next_parent",
            password="password123",
            email="approve_next@example.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="approve_next_child",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create recurring chore with new API
        chore_data = {
            "title": "Daily Task",
            "description": "Do this every day",
            "assignment_mode": "single",
            "assignee_ids": [child.id],
            "reward": 5.0,
            "cooldown_days": 1,
            "is_recurring": True
        }

        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data=chore_data
        )

        # Complete the chore
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Approve with next instance creation
        async with UnitOfWork(session_factory=test_uow_factory) as uow:
            result = await chore_service.approve_chore_with_next_instance(
                uow,
                chore_id=chore.id,
                parent_id=parent.id
            )
            await uow.commit()

        # Verify approval - check the chore object returned (has assignment fields populated)
        assert result["approved_chore"].is_approved is True
        assert result["approved_chore"].completion_date is not None

        # Verify next instance was created
        assert result["next_instance"] is not None
        next_chore = result["next_instance"]
        assert next_chore.title == "Daily Task"
        assert next_chore.assignment_mode == "single"

        # Verify next instance has an assignment for the same child
        from backend.app.models.chore_assignment import ChoreAssignment
        from sqlalchemy import select

        stmt = select(ChoreAssignment).where(ChoreAssignment.chore_id == next_chore.id)
        result_db = await db_session.execute(stmt)
        next_assignment = result_db.scalars().first()
        assert next_assignment is not None
        assert next_assignment.assignee_id == child.id
        assert next_assignment.is_completed is False
        assert next_assignment.is_approved is False
    
    @pytest.mark.asyncio
    async def test_approve_range_chore_with_next_instance(self, db_session: AsyncSession, test_uow_factory):
        """Test approving a range-based recurring chore."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="approve_range_parent",
            password="password123",
            email="approve_range@example.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="approve_range_child",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create range-based recurring chore with new API
        chore_data = {
            "title": "Variable Task",
            "description": "Reward varies",
            "assignment_mode": "single",
            "assignee_ids": [child.id],
            "reward": 10.0,  # Default reward
            "is_range_reward": True,
            "min_reward": 5.0,
            "max_reward": 15.0,
            "cooldown_days": 7,
            "is_recurring": True
        }

        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data=chore_data
        )

        # Complete the chore
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Approve with specific reward value
        async with UnitOfWork(session_factory=test_uow_factory) as uow:
            result = await chore_service.approve_chore_with_next_instance(
                uow,
                chore_id=chore.id,
                parent_id=parent.id,
                reward_value=10.0
            )
            await uow.commit()

        # Verify approval with correct reward - check the populated chore object
        assert result["approved_chore"].is_approved is True
        assert result["approved_chore"].approval_reward == 10.0

        # Verify next instance maintains range reward
        next_chore = result["next_instance"]
        assert next_chore.is_range_reward is True
        assert next_chore.min_reward == 5.0
        assert next_chore.max_reward == 15.0
    
    @pytest.mark.asyncio
    async def test_approve_non_recurring_chore(self, db_session: AsyncSession, test_uow_factory):
        """Test approving a non-recurring chore doesn't create next instance."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="approve_single_parent",
            password="password123",
            email="approve_single@example.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="approve_single_child",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create one-time chore with new API
        chore_data = {
            "title": "One Time Task",
            "description": "A one-time task",
            "assignment_mode": "single",
            "assignee_ids": [child.id],
            "reward": 20.0,
            "is_recurring": False
        }

        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data=chore_data
        )

        # Complete the chore
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Approve
        async with UnitOfWork(session_factory=test_uow_factory) as uow:
            result = await chore_service.approve_chore_with_next_instance(
                uow,
                chore_id=chore.id,
                parent_id=parent.id
            )
            await uow.commit()

        # Verify approval - check the populated chore object
        assert result["approved_chore"].is_approved is True

        # Verify no next instance was created
        assert result["next_instance"] is None
    
    @pytest.mark.asyncio
    async def test_bulk_assign_validation_error(self, db_session: AsyncSession, test_uow_factory):
        """Test bulk assignment with validation errors."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and another parent's child
        parent1 = await user_service.register_user(
            db_session,
            username="bulk_val_parent1",
            password="password123",
            email="bulk_val1@example.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="bulk_val_parent2",
            password="password123",
            email="bulk_val2@example.com",
            is_parent=True
        )
        
        # Create child for parent2
        other_child = await user_service.register_user(
            db_session,
            username="bulk_val_child",
            password="password123",
            is_parent=False,
            parent_id=parent2.id
        )
        
        # Try to assign chore to another parent's child
        assignments = [
            {
                "title": "Invalid Assignment",
                "assignee_id": other_child.id,  # Not parent1's child!
                "reward": 5.0
            }
        ]
        
        # Should fail with validation error
        with pytest.raises(Exception) as exc_info:
            async with UnitOfWork(session_factory=test_uow_factory) as uow:
                await chore_service.bulk_assign_chores(
                    uow,
                    creator_id=parent1.id,
                    assignments=assignments
                )
                await uow.commit()
        
        assert "does not belong to this parent" in str(exc_info.value)