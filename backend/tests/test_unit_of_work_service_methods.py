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


class TestUnitOfWorkServiceMethods:
    """Test service methods that use UnitOfWork for transactional operations."""
    
    @pytest.mark.asyncio
    async def test_bulk_assign_chores_success(self, db_session: AsyncSession):
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
        async with UnitOfWork() as uow:
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
        assert created_chores[0].assignee_id == child1.id
        assert created_chores[0].is_recurring is True
        
        assert created_chores[1].title == "Do Homework"
        assert created_chores[1].assignee_id == child2.id
        
        assert created_chores[2].title == "Walk Dog"
        assert created_chores[2].is_range_reward is True
        assert created_chores[2].min_reward == 2.0
        assert created_chores[2].max_reward == 5.0
    
    @pytest.mark.asyncio
    async def test_bulk_assign_chores_rollback_on_error(self, db_session: AsyncSession):
        """Test that bulk assignment rolls back on error."""
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
        
        # Create one child
        child = await user_service.register_user(
            db_session,
            username="bulk_error_child",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Prepare assignments with one invalid (non-existent child)
        assignments = [
            {
                "title": "Valid Chore",
                "assignee_id": child.id,
                "reward": 5.0
            },
            {
                "title": "Invalid Chore",
                "assignee_id": 99999,  # Non-existent child
                "reward": 10.0
            }
        ]
        
        # Try bulk assignment - should fail
        with pytest.raises(Exception):
            async with UnitOfWork() as uow:
                await chore_service.bulk_assign_chores(
                    uow,
                    creator_id=parent.id,
                    assignments=assignments
                )
                await uow.commit()
        
        # Verify no chores were created (transaction rolled back)
        chores = await chore_service.get_chores_for_user(db_session, user=parent)
        assert len(chores) == 0
    
    @pytest.mark.asyncio
    async def test_approve_chore_with_next_instance(self, db_session: AsyncSession):
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
        
        # Create recurring chore
        chore_data = {
            "title": "Daily Task",
            "description": "Do this every day",
            "assignee_id": child.id,
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
        async with UnitOfWork() as uow:
            result = await chore_service.approve_chore_with_next_instance(
                uow,
                chore_id=chore.id,
                parent_id=parent.id
            )
            await uow.commit()
        
        # Verify approval
        assert result["approved_chore"].is_approved is True
        assert result["approved_chore"].completion_date is not None
        
        # Verify next instance was created
        assert result["next_instance"] is not None
        next_chore = result["next_instance"]
        assert next_chore.title == "Daily Task"
        assert next_chore.is_completed is False
        assert next_chore.is_approved is False
        assert next_chore.assignee_id == child.id
    
    @pytest.mark.asyncio
    async def test_approve_range_chore_with_next_instance(self, db_session: AsyncSession):
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
        
        # Create range-based recurring chore
        chore_data = {
            "title": "Variable Task",
            "description": "Reward varies",
            "assignee_id": child.id,
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
        async with UnitOfWork() as uow:
            result = await chore_service.approve_chore_with_next_instance(
                uow,
                chore_id=chore.id,
                parent_id=parent.id,
                reward_value=10.0
            )
            await uow.commit()
        
        # Verify approval with correct reward
        assert result["approved_chore"].is_approved is True
        assert result["approved_chore"].reward == 10.0
        
        # Verify next instance maintains range reward
        next_chore = result["next_instance"]
        assert next_chore.is_range_reward is True
        assert next_chore.min_reward == 5.0
        assert next_chore.max_reward == 15.0
    
    @pytest.mark.asyncio
    async def test_approve_non_recurring_chore(self, db_session: AsyncSession):
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
        
        # Create one-time chore
        chore_data = {
            "title": "One Time Task",
            "assignee_id": child.id,
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
        async with UnitOfWork() as uow:
            result = await chore_service.approve_chore_with_next_instance(
                uow,
                chore_id=chore.id,
                parent_id=parent.id
            )
            await uow.commit()
        
        # Verify approval
        assert result["approved_chore"].is_approved is True
        
        # Verify no next instance was created
        assert result["next_instance"] is None
    
    @pytest.mark.asyncio
    async def test_bulk_assign_validation_error(self, db_session: AsyncSession):
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
            async with UnitOfWork() as uow:
                await chore_service.bulk_assign_chores(
                    uow,
                    creator_id=parent1.id,
                    assignments=assignments
                )
                await uow.commit()
        
        assert "does not belong to this parent" in str(exc_info.value)