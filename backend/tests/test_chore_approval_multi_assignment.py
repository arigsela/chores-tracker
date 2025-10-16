"""
Test ChoreService approval functionality for multi-assignment chores.

Tests the approval logic for all three assignment modes:
- single: Parent approves single child's assignment
- multi_independent: Parent approves each child's assignment independently
- unassigned: Parent approves any child who claimed the pool chore
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.repositories.chore_assignment import ChoreAssignmentRepository
from backend.app.repositories.reward_adjustment import RewardAdjustmentRepository


class TestChoreApprovalMultiAssignment:
    """Test multi-assignment chore approval business logic."""

    @pytest.mark.asyncio
    async def test_approve_single_mode_assignment(self, db_session: AsyncSession):
        """Test approving a single mode assignment."""
        user_service = UserService()
        chore_service = ChoreService()
        reward_repo = RewardAdjustmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_approve_single",
            password="password123",
            email="parentas@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_approve_single",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create and complete chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Clean Room",
                "description": "Test approval",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        assignment_id = completion_result["assignment"].id

        # Parent approves assignment
        result = await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id
        )

        # Verify approval result
        assert result["assignment"].is_approved is True
        assert result["assignment"].approval_date is not None
        assert result["final_reward"] == 5.0

        # Verify reward adjustment was created
        assert result["reward_adjustment"] is not None
        assert result["reward_adjustment"].amount == Decimal("5.0")
        assert result["reward_adjustment"].child_id == child.id
        assert result["reward_adjustment"].parent_id == parent.id

    @pytest.mark.asyncio
    async def test_approve_multi_independent_assignments(self, db_session: AsyncSession):
        """Test approving multiple independent assignments for same chore."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and three children
        parent = await user_service.register_user(
            db_session,
            username="parent_multi_approve",
            password="password123",
            email="parentma@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_multi_approve",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_multi_approve",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_multi_approve",
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

        # All three children complete
        result1 = await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child1.id)
        result2 = await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child2.id)
        result3 = await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child3.id)

        # Parent approves each assignment independently
        approval1 = await chore_service.approve_assignment(
            db_session,
            assignment_id=result1["assignment"].id,
            parent_id=parent.id
        )
        assert approval1["assignment"].assignee_id == child1.id
        assert approval1["assignment"].is_approved is True

        approval2 = await chore_service.approve_assignment(
            db_session,
            assignment_id=result2["assignment"].id,
            parent_id=parent.id
        )
        assert approval2["assignment"].assignee_id == child2.id
        assert approval2["assignment"].is_approved is True

        approval3 = await chore_service.approve_assignment(
            db_session,
            assignment_id=result3["assignment"].id,
            parent_id=parent.id
        )
        assert approval3["assignment"].assignee_id == child3.id
        assert approval3["assignment"].is_approved is True

        # Verify all three got their rewards
        assert approval1["reward_adjustment"].amount == Decimal("10.0")
        assert approval2["reward_adjustment"].amount == Decimal("10.0")
        assert approval3["reward_adjustment"].amount == Decimal("10.0")

    @pytest.mark.asyncio
    async def test_approve_unassigned_pool_assignment(self, db_session: AsyncSession):
        """Test approving a claimed pool chore."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_pool_approve",
            password="password123",
            email="parentpa@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_pool_approve",
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
                "description": "Pool chore",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []
            }
        )

        # Child claims and completes
        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Parent approves
        approval_result = await chore_service.approve_assignment(
            db_session,
            assignment_id=completion_result["assignment"].id,
            parent_id=parent.id
        )

        assert approval_result["assignment"].is_approved is True
        assert approval_result["reward_adjustment"].amount == Decimal("3.0")

    @pytest.mark.asyncio
    async def test_approve_with_range_reward(self, db_session: AsyncSession):
        """Test approving assignment with range-based reward."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_approve",
            password="password123",
            email="parentra@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_range_approve",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with range reward
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Mow the Lawn",
                "description": "Quality-based reward",
                "is_range_reward": True,
                "min_reward": 5.0,
                "max_reward": 15.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Child completes
        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Parent approves with reward value of 12.0
        approval_result = await chore_service.approve_assignment(
            db_session,
            assignment_id=completion_result["assignment"].id,
            parent_id=parent.id,
            reward_value=12.0
        )

        # Verify custom reward was used
        assert approval_result["final_reward"] == 12.0
        assert approval_result["assignment"].approval_reward == 12.0
        assert approval_result["reward_adjustment"].amount == Decimal("12.0")

    @pytest.mark.asyncio
    async def test_cannot_approve_uncompleted_assignment(self, db_session: AsyncSession):
        """Test that uncompleted assignment cannot be approved."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_uncompleted",
            password="password123",
            email="parentuc@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_uncompleted",
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

        # Get assignment ID (not completed yet)
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assignment_id = assignments[0].id

        # Try to approve without completion (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=assignment_id,
                parent_id=parent.id
            )

        assert exc_info.value.status_code == 400
        assert "must be completed" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_cannot_approve_twice(self, db_session: AsyncSession):
        """Test that assignment cannot be approved twice."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_twice_approve",
            password="password123",
            email="parentta@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_twice_approve",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create and complete chore
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

        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        assignment_id = completion_result["assignment"].id

        # Approve once
        await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id
        )

        # Try to approve again (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=assignment_id,
                parent_id=parent.id
            )

        assert exc_info.value.status_code == 400
        assert "already approved" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_range_reward_requires_value(self, db_session: AsyncSession):
        """Test that range reward requires reward_value parameter."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_req",
            password="password123",
            email="parentrr@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_range_req",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with range reward
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Range Chore",
                "description": "Test",
                "is_range_reward": True,
                "min_reward": 3.0,
                "max_reward": 10.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Child completes
        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Try to approve without reward_value (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=completion_result["assignment"].id,
                parent_id=parent.id
                # Missing reward_value!
            )

        assert exc_info.value.status_code == 422
        assert "reward value is required" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_range_reward_validates_bounds(self, db_session: AsyncSession):
        """Test that range reward value must be within min/max bounds."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_bounds",
            password="password123",
            email="parentrb@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_range_bounds",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with range reward (5-15)
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Range Chore",
                "description": "Test",
                "is_range_reward": True,
                "min_reward": 5.0,
                "max_reward": 15.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Child completes
        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Try to approve with value too low (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=completion_result["assignment"].id,
                parent_id=parent.id,
                reward_value=3.0  # Below min!
            )

        assert exc_info.value.status_code == 422
        assert "between" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_cannot_approve_from_different_family(self, db_session: AsyncSession):
        """Test that parent from different family cannot approve."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_diff_family",
            password="password123",
            email="parent1df@test.com",
            is_parent=True
        )

        parent2 = await user_service.register_user(
            db_session,
            username="parent2_diff_family",
            password="password123",
            email="parent2df@test.com",
            is_parent=True
        )

        # Create child for parent1
        child = await user_service.register_user(
            db_session,
            username="child_diff_family",
            password="password123",
            is_parent=False,
            parent_id=parent1.id
        )

        # Parent1 creates and child completes chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent1.id,
            chore_data={
                "title": "Test Chore",
                "description": "Test",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        completion_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Parent2 tries to approve (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=completion_result["assignment"].id,
                parent_id=parent2.id
            )

        assert exc_info.value.status_code == 403
        assert "you created" in str(exc_info.value.detail).lower() or "your family" in str(exc_info.value.detail).lower()
