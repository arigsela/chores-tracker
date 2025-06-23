"""
Test ChoreService edge cases.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.chore_service import ChoreService
from backend.app.services.user_service import UserService
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash


class TestChoreServiceEdgeCases:
    """Test ChoreService edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_chore_in_cooldown(self, db_session: AsyncSession):
        """Test completing a recurring chore that's in cooldown."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_cooldown",
            password="password123",
            email="cooldown@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_cooldown",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create recurring chore with cooldown
        chore = Chore(
            title="Recurring Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=7,  # 7 day cooldown
            is_recurring=True,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=True,  # Already completed
            is_approved=True,
            is_disabled=False,
            completion_date=datetime.utcnow() - timedelta(days=3)  # 3 days ago
        )
        db_session.add(chore)
        await db_session.commit()
        
        # Try to complete again (should fail - in cooldown)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )
        
        assert exc_info.value.status_code == 400
        assert "cooldown" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_complete_chore_after_cooldown(self, db_session: AsyncSession):
        """Test completing a recurring chore after cooldown expires."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_after_cd",
            password="password123",
            email="after_cd@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_after_cd",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create recurring chore with cooldown (completed 8 days ago)
        chore = Chore(
            title="Recurring Chore After",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=7,  # 7 day cooldown
            is_recurring=True,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=True,
            is_approved=True,
            is_disabled=False,
            completion_date=datetime.utcnow() - timedelta(days=8)  # 8 days ago
        )
        db_session.add(chore)
        await db_session.commit()
        
        # Complete again (should succeed - cooldown expired)
        updated = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        
        assert updated.is_completed is True
        assert updated.is_approved is False  # Reset to pending
    
    @pytest.mark.asyncio
    async def test_approve_range_reward_missing_value(self, db_session: AsyncSession):
        """Test approving range reward without specifying value."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_miss",
            password="password123",
            email="range_miss@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_range_miss",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create range reward chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Range Reward Chore",
                "description": "Test",
                "reward": 0,  # Not used for range
                "min_reward": 5.0,
                "max_reward": 15.0,
                "is_range_reward": True,
                "assignee_id": child.id
            }
        )
        
        # Complete it
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        
        # Try to approve without reward_value
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent.id
                # Missing reward_value!
            )
        
        assert exc_info.value.status_code == 422
        assert "reward value" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_approve_range_reward_out_of_bounds(self, db_session: AsyncSession):
        """Test approving range reward with value outside bounds."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_oob",
            password="password123",
            email="range_oob@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_range_oob",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create range reward chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Range Bounds Chore",
                "description": "Test",
                "reward": 0,
                "min_reward": 5.0,
                "max_reward": 15.0,
                "is_range_reward": True,
                "assignee_id": child.id
            }
        )
        
        # Complete it
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        
        # Try to approve with value too high
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent.id,
                reward_value=20.0  # Above max!
            )
        
        assert exc_info.value.status_code == 422
        assert "between" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_create_chore_invalid_range_bounds(self, db_session: AsyncSession):
        """Test creating chore with invalid range bounds."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_bad_range",
            password="password123",
            email="bad_range@test.com",
            is_parent=True
        )
        
        # Try to create with min > max
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Bad Range Chore",
                    "description": "Test",
                    "reward": 0,
                    "min_reward": 20.0,  # Higher than max!
                    "max_reward": 10.0,
                    "is_range_reward": True
                }
            )
        
        assert exc_info.value.status_code == 422
        assert "min_reward must be less than max_reward" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_chore_assignee_different_parent(self, db_session: AsyncSession):
        """Test updating chore to assign to child of different parent."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_update",
            password="password123",
            email="parent1_upd@test.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_update",
            password="password123",
            email="parent2_upd@test.com",
            is_parent=True
        )
        
        # Create children
        child1 = await user_service.register_user(
            db_session,
            username="child1_update",
            password="password123",
            is_parent=False,
            parent_id=parent1.id
        )
        
        child2 = await user_service.register_user(
            db_session,
            username="child2_update",
            password="password123",
            is_parent=False,
            parent_id=parent2.id
        )
        
        # Parent1 creates chore for child1
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent1.id,
            chore_data={
                "title": "Update Assignee Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": child1.id
            }
        )
        
        # Try to update to child2 (different parent)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.update_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent1.id,
                update_data={"assignee_id": child2.id}
            )
        
        assert exc_info.value.status_code == 403
        assert "can only assign chores to your own children" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_complete_unassigned_chore(self, db_session: AsyncSession):
        """Test completing a chore that has no assignee."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_unassign",
            password="password123",
            email="unassign@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_unassign",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create unassigned chore
        chore = Chore(
            title="Unassigned Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=None,  # No assignee!
            is_completed=False,
            is_approved=False,
            is_disabled=False
        )
        db_session.add(chore)
        await db_session.commit()
        
        # Try to complete it
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )
        
        assert exc_info.value.status_code == 403
        assert "not the assignee" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_approve_already_approved_chore(self, db_session: AsyncSession):
        """Test approving an already approved chore."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_double_app",
            password="password123",
            email="double_app@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_double_app",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create and complete chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Double Approve Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": child.id
            }
        )
        
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        
        # Approve once
        await chore_service.approve_chore(
            db_session,
            chore_id=chore.id,
            parent_id=parent.id
        )
        
        # Try to approve again
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent.id
            )
        
        assert exc_info.value.status_code == 400
        assert "already approved" in str(exc_info.value.detail).lower()