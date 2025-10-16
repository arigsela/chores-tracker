"""
Test ChoreService rejection functionality for multi-assignment chores.

Tests the rejection logic for all three assignment modes:
- single: Parent rejects child's assignment
- multi_independent: Parent rejects one child's assignment, others unaffected
- unassigned: Parent rejects pool chore claim
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.repositories.chore_assignment import ChoreAssignmentRepository


class TestChoreRejectionMultiAssignment:
    """Test multi-assignment chore rejection business logic."""

    @pytest.mark.asyncio
    async def test_reject_single_mode_assignment(self, db_session: AsyncSession):
        """Test rejecting a single mode assignment with reason."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_reject_single",
            password="password123",
            email="parentrs@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_reject_single",
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
                "description": "Not done properly",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Child completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment = result["assignment"]

        # Parent rejects
        rejection_result = await chore_service.reject_assignment(
            db_session,
            assignment_id=assignment.id,
            parent_id=parent.id,
            rejection_reason="The room is still messy. Please vacuum under the bed."
        )

        # Verify rejection
        assert rejection_result["assignment"].is_completed is False
        assert rejection_result["assignment"].completion_date is None
        assert rejection_result["assignment"].is_approved is False
        assert rejection_result["assignment"].rejection_reason == "The room is still messy. Please vacuum under the bed."
        assert rejection_result["rejection_reason"] == "The room is still messy. Please vacuum under the bed."
        assert "redo the chore" in rejection_result["message"]

    @pytest.mark.asyncio
    async def test_reject_multi_independent_assignment(self, db_session: AsyncSession):
        """Test rejecting one child's assignment doesn't affect others."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and three children
        parent = await user_service.register_user(
            db_session,
            username="parent_reject_multi",
            password="password123",
            email="parentrm@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_reject_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_reject_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_reject_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create multi-independent chore
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

        # Parent rejects child1's work
        rejection = await chore_service.reject_assignment(
            db_session,
            assignment_id=result1["assignment"].id,
            parent_id=parent.id,
            rejection_reason="Toys still on the floor"
        )

        # Verify child1's assignment is rejected
        assert rejection["assignment"].assignee_id == child1.id
        assert rejection["assignment"].is_completed is False
        assert rejection["assignment"].rejection_reason == "Toys still on the floor"

        # Verify other assignments still completed (pending approval)
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        child2_assignment = next(a for a in assignments if a.assignee_id == child2.id)
        child3_assignment = next(a for a in assignments if a.assignee_id == child3.id)

        assert child2_assignment.is_completed is True
        assert child2_assignment.is_approved is False
        assert child3_assignment.is_completed is True
        assert child3_assignment.is_approved is False

    @pytest.mark.asyncio
    async def test_reject_unassigned_pool_assignment(self, db_session: AsyncSession):
        """Test rejecting a pool chore assignment."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_reject_pool",
            password="password123",
            email="parentrp@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_reject_pool",
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
                "description": "Take dog around the block",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []
            }
        )

        # Child claims and completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Parent rejects
        rejection = await chore_service.reject_assignment(
            db_session,
            assignment_id=result["assignment"].id,
            parent_id=parent.id,
            rejection_reason="You only walked halfway down the street"
        )

        # Verify rejection
        assert rejection["assignment"].is_completed is False
        assert rejection["assignment"].rejection_reason == "You only walked halfway down the street"

    @pytest.mark.asyncio
    async def test_cannot_reject_uncompleted_assignment(self, db_session: AsyncSession):
        """Test that uncompleted assignments cannot be rejected."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_reject_uncompleted",
            password="password123",
            email="parentru@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_reject_uncompleted",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore (not completed)
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

        # Get the assignment
        assignment_repo = ChoreAssignmentRepository()
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assignment = assignments[0]

        # Try to reject uncompleted assignment (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.reject_assignment(
                db_session,
                assignment_id=assignment.id,
                parent_id=parent.id,
                rejection_reason="Test reason"
            )

        assert exc_info.value.status_code == 400
        assert "must be completed before rejection" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_cannot_reject_approved_assignment(self, db_session: AsyncSession):
        """Test that approved assignments cannot be rejected."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_reject_approved",
            password="password123",
            email="parentra@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_reject_approved",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create, complete, and approve chore
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

        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        await chore_service.approve_assignment(
            db_session,
            assignment_id=result["assignment"].id,
            parent_id=parent.id
        )

        # Try to reject approved assignment (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.reject_assignment(
                db_session,
                assignment_id=result["assignment"].id,
                parent_id=parent.id,
                rejection_reason="Changed my mind"
            )

        assert exc_info.value.status_code == 400
        assert "cannot reject already approved" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_rejection_requires_non_empty_reason(self, db_session: AsyncSession):
        """Test that rejection reason is required and cannot be empty."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_empty_reason",
            password="password123",
            email="parenter@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_empty_reason",
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

        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Try to reject with empty reason (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.reject_assignment(
                db_session,
                assignment_id=result["assignment"].id,
                parent_id=parent.id,
                rejection_reason="   "  # Only whitespace
            )

        assert exc_info.value.status_code == 422
        assert "rejection reason is required" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_cannot_reject_from_different_family(self, db_session: AsyncSession):
        """Test that parent from different family cannot reject assignment."""
        user_service = UserService()
        chore_service = ChoreService()
        from backend.app.repositories.user import UserRepository
        from backend.app.repositories.family import FamilyRepository

        # Create two families
        family_repo = FamilyRepository()

        family1 = await family_repo.create(db_session, obj_in={"name": "Family 1", "invite_code": "FAM1CODE"})
        family2 = await family_repo.create(db_session, obj_in={"name": "Family 2", "invite_code": "FAM2CODE"})

        # Create parent1 in family1
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_diff_family_reject",
            password="password123",
            email="parent1dfr@test.com",
            is_parent=True
        )

        # Assign to family1
        user_repo = UserRepository()
        await user_repo.update(db_session, id=parent1.id, obj_in={"family_id": family1.id})

        # Create child1 in family1
        child1 = await user_service.register_user(
            db_session,
            username="child1_diff_family_reject",
            password="password123",
            is_parent=False,
            parent_id=parent1.id
        )
        await user_repo.update(db_session, id=child1.id, obj_in={"family_id": family1.id})

        # Create parent2 in family2
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_diff_family_reject",
            password="password123",
            email="parent2dfr@test.com",
            is_parent=True
        )
        await user_repo.update(db_session, id=parent2.id, obj_in={"family_id": family2.id})

        # Parent1 creates chore for child1
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent1.id,
            chore_data={
                "title": "Family 1 Chore",
                "description": "Test",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child1.id]
            }
        )

        # Child1 completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child1.id
        )

        # Parent2 tries to reject (should fail - different family)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.reject_assignment(
                db_session,
                assignment_id=result["assignment"].id,
                parent_id=parent2.id,
                rejection_reason="Not your family"
            )

        assert exc_info.value.status_code == 403
        assert "your family" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_child_can_redo_after_rejection(self, db_session: AsyncSession):
        """Test that child can redo chore after rejection."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_redo",
            password="password123",
            email="parentredo@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_redo",
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

        # Child completes first time
        result1 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Parent rejects
        await chore_service.reject_assignment(
            db_session,
            assignment_id=result1["assignment"].id,
            parent_id=parent.id,
            rejection_reason="Not good enough"
        )

        # Child redoes and completes again (should succeed)
        result2 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Verify second completion
        assert result2["assignment"].is_completed is True
        assert result2["assignment"].is_approved is False
        assert result2["assignment"].completion_date is not None

        # Note: The rejection_reason field remains from the previous rejection
        # This is intentional - it provides historical context. The is_completed
        # status is what determines the current state of the assignment.

    @pytest.mark.asyncio
    async def test_rejection_preserves_rejection_reason(self, db_session: AsyncSession):
        """Test that rejection reason is preserved for child to see."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_preserve_reason",
            password="password123",
            email="parentpr@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_preserve_reason",
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

        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )

        # Parent rejects with specific reason
        detailed_reason = "The dishes are not clean. Please rewash them with hot water and soap."
        await chore_service.reject_assignment(
            db_session,
            assignment_id=result["assignment"].id,
            parent_id=parent.id,
            rejection_reason=detailed_reason
        )

        # Get assignment and verify reason is preserved
        assignment = await assignment_repo.get(db_session, id=result["assignment"].id)
        assert assignment.rejection_reason == detailed_reason
        assert assignment.is_completed is False
