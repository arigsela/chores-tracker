"""
Test ChoreService completion functionality for multi-assignment chores.

Tests the completion logic for all three assignment modes:
- single: One child completes their assignment
- multi_independent: Multiple children complete independently
- unassigned: Any child can claim and complete from pool
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.repositories.chore_assignment import ChoreAssignmentRepository


class TestChoreCompletionMultiAssignment:
    """Test multi-assignment chore completion business logic."""

    @pytest.mark.asyncio
    async def test_complete_single_mode_chore(self, db_session: AsyncSession):
        """Test completing a chore in single assignment mode."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_single_complete",
            password="password123",
            email="parentsc@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_single_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with single mode
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Single Mode Chore",
                "description": "Test completion",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Child completes chore
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Verify result structure
        assert result is not None
        assert "chore" in result
        assert "assignment" in result
        assert "message" in result

        # Verify assignment was marked complete
        assignment = result["assignment"]
        assert assignment.is_completed is True
        assert assignment.is_approved is False
        assert assignment.completion_date is not None
        assert assignment.assignee_id == child.id

    @pytest.mark.asyncio
    async def test_complete_multi_independent_mode(self, db_session: AsyncSession):
        """Test that in multi_independent mode, completions are independent."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and three children
        parent = await user_service.register_user(
            db_session,
            username="parent_multi_complete",
            password="password123",
            email="parentmc@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_multi_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_multi_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_multi_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with multi_independent mode
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Clean Your Room",
                "description": "Each child cleans their own room",
                "reward": 10.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id, child3.id]
            }
        )

        # Child1 completes their assignment
        result1 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child1.id
        )

        # Verify child1's assignment is completed
        assert result1["assignment"].assignee_id == child1.id
        assert result1["assignment"].is_completed is True

        # Verify other assignments still pending
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        child2_assignment = next(a for a in assignments if a.assignee_id == child2.id)
        child3_assignment = next(a for a in assignments if a.assignee_id == child3.id)

        assert child2_assignment.is_completed is False
        assert child3_assignment.is_completed is False

        # Child2 and Child3 can still complete independently
        result2 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child2.id
        )
        assert result2["assignment"].assignee_id == child2.id
        assert result2["assignment"].is_completed is True

        result3 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child3.id
        )
        assert result3["assignment"].assignee_id == child3.id
        assert result3["assignment"].is_completed is True

    @pytest.mark.asyncio
    async def test_complete_unassigned_pool_chore(self, db_session: AsyncSession):
        """Test claiming and completing an unassigned pool chore."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and two children
        parent = await user_service.register_user(
            db_session,
            username="parent_unassigned_complete",
            password="password123",
            email="parentuc@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_unassigned_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_unassigned_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create unassigned pool chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Walk the Dog",
                "description": "Anyone can do this",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []
            }
        )

        # Verify no assignments initially
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 0

        # Child1 claims and completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child1.id
        )

        # Verify assignment was created and completed
        assert result["assignment"].assignee_id == child1.id
        assert result["assignment"].is_completed is True
        assert result["assignment"].is_approved is False

        # Verify child2 cannot complete (already claimed)
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 1
        assert assignments[0].assignee_id == child1.id

    @pytest.mark.asyncio
    async def test_cannot_complete_without_assignment(self, db_session: AsyncSession):
        """Test that child without assignment cannot complete single/multi mode chore."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and two children
        parent = await user_service.register_user(
            db_session,
            username="parent_no_assign",
            password="password123",
            email="parentna@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_no_assign",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_no_assign",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore assigned only to child1
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Child1 Only",
                "description": "Test",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child1.id]
            }
        )

        # Child2 tries to complete (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child2.id
            )

        assert exc_info.value.status_code == 403
        assert "not assigned" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_cannot_complete_twice_before_approval(self, db_session: AsyncSession):
        """Test that child cannot complete same assignment twice before approval."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_twice",
            password="password123",
            email="parenttwice@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_twice",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Test Chore",
                "description": "Test",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete once
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Try to complete again (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )

        assert exc_info.value.status_code == 400
        assert "already completed" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_cannot_complete_disabled_chore(self, db_session: AsyncSession):
        """Test that disabled chores cannot be completed."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_disabled_complete",
            password="password123",
            email="parentdc@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_disabled_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create and disable chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Disabled Chore",
                "description": "Test",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Disable the chore
        await chore_service.disable_chore(
            db_session,
            chore_id=chore.id,
            parent_id=parent.id
        )

        # Try to complete (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )

        assert exc_info.value.status_code == 400
        assert "disabled" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_recurring_chore_cooldown(self, db_session: AsyncSession):
        """Test cooldown period for recurring chores."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_cooldown",
            password="password123",
            email="parentcooldown@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_cooldown",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create recurring chore with 7-day cooldown
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Weekly Chore",
                "description": "Test cooldown",
                "reward": 10.0,
                "is_recurring": True,
                "cooldown_days": 7,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete chore
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Manually approve and set approval_date in the past (to simulate approved chore)
        assignment = result["assignment"]
        past_date = datetime.utcnow() - timedelta(days=3)  # 3 days ago
        await assignment_repo.update(
            db_session,
            id=assignment.id,
            obj_in={
                "is_approved": True,
                "approval_date": past_date
            }
        )

        # Try to complete again (should fail - still in cooldown)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )

        assert exc_info.value.status_code == 400
        assert "cooldown" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_recurring_chore_after_cooldown(self, db_session: AsyncSession):
        """Test that recurring chore can be completed after cooldown expires."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_after_cooldown",
            password="password123",
            email="parentac@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_after_cooldown",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create recurring chore with 1-day cooldown
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Daily Chore",
                "description": "Test after cooldown",
                "reward": 5.0,
                "is_recurring": True,
                "cooldown_days": 1,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete chore first time
        result1 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Approve with approval_date 2 days ago (past cooldown)
        assignment = result1["assignment"]
        past_date = datetime.utcnow() - timedelta(days=2)
        await assignment_repo.update(
            db_session,
            id=assignment.id,
            obj_in={
                "is_approved": True,
                "approval_date": past_date
            }
        )

        # Complete again (should succeed - cooldown expired)
        result2 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Verify second completion succeeded
        assert result2["assignment"].is_completed is True
        assert result2["assignment"].is_approved is False
        assert result2["assignment"].completion_date is not None
