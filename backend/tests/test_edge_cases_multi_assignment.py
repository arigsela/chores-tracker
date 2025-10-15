"""
Edge case tests for multi-assignment chores feature.

Phase 6.3 requirements coverage:
1. Test: delete child with pending assignments (cascade)
2. Test: delete chore with pending assignments (cascade)
3. Test: approve already-approved assignment (idempotent)
4. Test: single mode with 0 or 2+ assignees (validation error)
5. Test: reward_value outside min/max range (validation error)
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.models.chore_assignment import ChoreAssignment
from backend.app.models.chore import Chore


class TestDeleteChildWithPendingAssignments:
    """Test CASCADE delete behavior when deleting a child with pending assignments."""

    @pytest.mark.asyncio
    async def test_delete_child_cascades_to_assignments(
        self,
        db_session: AsyncSession
    ):
        """
        Test that deleting a child also deletes their pending assignments.
        Phase 6.3 Requirement #1

        Note: SQLite test database has CASCADE DELETE enabled via foreign keys.
        When a child is deleted, all their assignments and activities are also deleted.
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_del_child",
            password="password123",
            email="parent_del_child@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_del_child",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with single mode (no activity logging to avoid user_id constraint)
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Test Chore for Cascade",
                "description": "Testing cascade delete",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Reload chore with assignments
        chore = await chore_service.repository.get_with_assignments(db_session, chore_id=chore.id)
        assert len(chore.assignments) == 1
        assignment_id = chore.assignments[0].id

        # Verify assignment exists
        assignment = await db_session.get(ChoreAssignment, assignment_id)
        assert assignment is not None

        # Delete the child (CASCADE will delete assignments and activities)
        await db_session.delete(child)
        await db_session.commit()

        # Verify assignment was CASCADE deleted
        assignment_after_delete = await db_session.get(ChoreAssignment, assignment_id)
        assert assignment_after_delete is None

        # Verify chore still exists (only assignment deleted)
        chore_after_delete = await db_session.get(Chore, chore.id)
        assert chore_after_delete is not None


class TestDeleteChoreWithPendingAssignments:
    """Test CASCADE delete behavior when deleting a chore with pending assignments."""

    @pytest.mark.asyncio
    async def test_delete_chore_cascades_to_assignments(
        self,
        db_session: AsyncSession
    ):
        """
        Test that deleting a chore also deletes all its assignments.
        Phase 6.3 Requirement #2
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and 3 children
        parent = await user_service.register_user(
            db_session,
            username="parent_del_chore",
            password="password123",
            email="parent_del_chore@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_del_chore",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_del_chore",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_del_chore",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create multi_independent chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Test Multi Chore",
                "description": "Testing cascade delete",
                "reward": 5.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id, child3.id]
            }
        )

        # Reload chore with assignments
        chore = await chore_service.repository.get_with_assignments(db_session, chore_id=chore.id)
        assert len(chore.assignments) == 3
        assignment_ids = [a.id for a in chore.assignments]

        # Have one child complete their assignment
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child1.id
        )

        # Verify all assignments exist
        for assignment_id in assignment_ids:
            assignment = await db_session.get(ChoreAssignment, assignment_id)
            assert assignment is not None

        # Delete the chore
        await db_session.delete(chore)
        await db_session.commit()

        # Verify all assignments were CASCADE deleted
        for assignment_id in assignment_ids:
            assignment_after_delete = await db_session.get(ChoreAssignment, assignment_id)
            assert assignment_after_delete is None

        # Verify children still exist
        for child_id in [child1.id, child2.id, child3.id]:
            child_after_delete = await user_service.repository.get(db_session, id=child_id)
            assert child_after_delete is not None


class TestIdempotentApproval:
    """Test that approving an already-approved assignment is handled gracefully."""

    @pytest.mark.asyncio
    async def test_approve_already_approved_assignment_is_idempotent(
        self,
        db_session: AsyncSession
    ):
        """
        Test that re-approving an already-approved assignment doesn't fail.
        Phase 6.3 Requirement #3
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_idempotent",
            password="password123",
            email="parent_idempotent@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_idempotent",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create and complete chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Test Idempotent",
                "description": "Testing",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment_id = result["assignment"].id

        # First approval
        result1 = await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id
        )
        assert result1["assignment"].is_approved is True

        # Second approval (should handle gracefully, not raise exception)
        # The service should either:
        # 1. Return success with message "already approved"
        # 2. Raise a validation exception
        # Let's test that it doesn't crash
        try:
            result2 = await chore_service.approve_assignment(
                db_session,
                assignment_id=assignment_id,
                parent_id=parent.id
            )
            # If it succeeds, verify assignment is still approved
            assert result2["assignment"].is_approved is True
        except Exception as exc:
            # If it raises, verify it's a validation error (not a crash)
            assert "already" in str(exc).lower() or "approved" in str(exc).lower()


class TestAssignmentModeValidation:
    """Test validation errors for invalid assignment modes."""

    @pytest.mark.asyncio
    async def test_single_mode_with_zero_assignees_raises_error(
        self,
        db_session: AsyncSession
    ):
        """
        Test that single mode with 0 assignees raises validation error.
        Phase 6.3 Requirement #4a
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_val_zero",
            password="password123",
            email="parent_val_zero@test.com",
            is_parent=True
        )

        # Try to create single mode chore with 0 assignees
        with pytest.raises(Exception) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Invalid Single Mode",
                    "description": "Should fail",
                    "reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": []
                }
            )

        # Verify error message mentions validation
        assert "single" in str(exc_info.value).lower() or "exactly" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_single_mode_with_multiple_assignees_raises_error(
        self,
        db_session: AsyncSession
    ):
        """
        Test that single mode with 2+ assignees raises validation error.
        Phase 6.3 Requirement #4b
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and 2 children
        parent = await user_service.register_user(
            db_session,
            username="parent_val_multi",
            password="password123",
            email="parent_val_multi@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_val_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_val_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Try to create single mode chore with 2 assignees
        with pytest.raises(Exception) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Invalid Single Mode",
                    "description": "Should fail",
                    "reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": [child1.id, child2.id]
                }
            )

        # Verify error message mentions validation
        assert "single" in str(exc_info.value).lower() or "exactly" in str(exc_info.value).lower()


class TestRangeRewardValidation:
    """Test validation errors for reward_value outside min/max range."""

    @pytest.mark.asyncio
    async def test_reward_value_below_minimum_raises_error(
        self,
        db_session: AsyncSession
    ):
        """
        Test that reward_value < min_reward raises validation error.
        Phase 6.3 Requirement #5a
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_low",
            password="password123",
            email="parent_range_low@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_range_low",
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
                "description": "Testing",
                "reward": 10.0,
                "is_range_reward": True,
                "min_reward": 5.0,
                "max_reward": 15.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete the chore
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment_id = result["assignment"].id

        # Try to approve with reward below minimum
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=assignment_id,
                parent_id=parent.id,
                reward_value=3.0  # Below min_reward of 5.0
            )

        # Verify error message mentions range validation
        assert "between" in str(exc_info.value.detail).lower() or "minimum" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_reward_value_above_maximum_raises_error(
        self,
        db_session: AsyncSession
    ):
        """
        Test that reward_value > max_reward raises validation error.
        Phase 6.3 Requirement #5b
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_high",
            password="password123",
            email="parent_range_high@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_range_high",
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
                "description": "Testing",
                "reward": 10.0,
                "is_range_reward": True,
                "min_reward": 5.0,
                "max_reward": 15.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete the chore
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment_id = result["assignment"].id

        # Try to approve with reward above maximum
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=assignment_id,
                parent_id=parent.id,
                reward_value=20.0  # Above max_reward of 15.0
            )

        # Verify error message mentions range validation
        assert "between" in str(exc_info.value.detail).lower() or "maximum" in str(exc_info.value.detail).lower()
