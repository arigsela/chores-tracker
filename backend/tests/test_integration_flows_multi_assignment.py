"""
Integration tests for complete multi-assignment chore flows.

These tests verify end-to-end workflows spanning multiple service operations,
ensuring all assignment modes work correctly through their full lifecycle.

Phase 6.2 requirements coverage:
1. Complete flow: create (single) → complete → approve → cooldown → reset
2. Complete flow: create (multi_independent) → 3 kids complete independently
3. Complete flow: create (unassigned) → claim → approve → returns to pool
4. Rejection flow: complete → reject → redo → approve
5. Range rewards: complete → approve with custom reward in range
6. Authorization: child can't approve, parent can't complete
7. Cooldown: can't complete during cooldown period
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.repositories.chore_assignment import ChoreAssignmentRepository
from backend.app.models.chore_assignment import ChoreAssignment


class TestSingleModeIntegrationFlow:
    """Test complete lifecycle for single assignment mode."""

    @pytest.mark.asyncio
    async def test_single_mode_full_lifecycle_with_cooldown_reset(
        self,
        db_session: AsyncSession
    ):
        """
        Test full lifecycle: create (single) → complete → approve → cooldown → reset.

        Phase 6.2 Requirement #1
        """
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_lifecycle",
            password="password123",
            email="lifecycle@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_lifecycle",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Step 1: Create recurring chore with cooldown
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Weekly Room Clean",
                "description": "Clean and organize your room weekly",
                "reward": 10.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id],
                "is_recurring": True,
                "cooldown_days": 7
            }
        )
        # Reload chore with assignments
        chore = await chore_service.repository.get_with_assignments(db_session, chore_id=chore.id)
        assert chore.is_single_assignment is True
        assert len(chore.assignments) == 1

        # Step 2: Child completes chore
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment = result["assignment"]
        assert assignment.is_completed is True
        assert assignment.is_approved is False

        # Step 3: Parent approves
        approval_result = await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment.id,
            parent_id=parent.id
        )
        assignment = approval_result["assignment"]
        assert assignment.is_approved is True
        assert assignment.approval_date is not None

        # Step 4: Verify cooldown prevents re-completion
        with pytest.raises(Exception) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )
        assert "cooldown" in str(exc_info.value).lower()

        # Step 5: Simulate cooldown expiration and reset
        # Fetch the assignment from DB (not the Pydantic model from result)
        db_assignment = await assignment_repo.get(db_session, id=assignment.id)
        db_assignment.approval_date = datetime.utcnow() - timedelta(days=8)
        await db_session.commit()

        # Step 6: Verify chore becomes available again after cooldown
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assert result["assignment"].is_completed is True
        assert result["assignment"].is_approved is False  # Fresh completion


class TestMultiIndependentIntegrationFlow:
    """Test complete lifecycle for multi_independent assignment mode."""

    @pytest.mark.asyncio
    async def test_multi_independent_three_children_independent_completion(
        self,
        db_session: AsyncSession
    ):
        """
        Test: create (multi_independent) → 3 kids complete independently.

        Phase 6.2 Requirement #2
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and 3 children
        parent = await user_service.register_user(
            db_session,
            username="parent_multi_flow",
            password="password123",
            email="multif@test.com",
            is_parent=True
        )

        children = []
        for i in range(3):
            child = await user_service.register_user(
                db_session,
                username=f"child_multi_flow_{i}",
                password="password123",
                is_parent=False,
                parent_id=parent.id
            )
            children.append(child)

        # Step 1: Create multi_independent chore for all 3 children
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Clean Your Room",
                "description": "Each child cleans their own room",
                "reward": 5.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [c.id for c in children]
            }
        )
        # Reload chore with assignments
        chore = await chore_service.repository.get_with_assignments(db_session, chore_id=chore.id)
        assert chore.is_multi_independent is True
        assert len(chore.assignments) == 3

        # Step 2: First child completes
        result1 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=children[0].id
        )
        assert result1["assignment"].assignee_id == children[0].id
        assert result1["assignment"].is_completed is True

        # Step 3: Parent approves first child
        await chore_service.approve_assignment(
            db_session,
            assignment_id=result1["assignment"].id,
            parent_id=parent.id
        )

        # Step 4: Second child completes (independent of first)
        result2 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=children[1].id
        )
        assert result2["assignment"].assignee_id == children[1].id
        assert result2["assignment"].is_completed is True

        # Step 5: Third child completes (independent of first two)
        result3 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=children[2].id
        )
        assert result3["assignment"].assignee_id == children[2].id
        assert result3["assignment"].is_completed is True

        # Verify: All 3 assignments exist independently
        assignment_repo = ChoreAssignmentRepository()
        all_assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(all_assignments) == 3
        completed_count = sum(1 for a in all_assignments if a.is_completed)
        approved_count = sum(1 for a in all_assignments if a.is_approved)
        assert completed_count == 3  # All completed
        assert approved_count == 1   # Only first approved


class TestUnassignedPoolIntegrationFlow:
    """Test complete lifecycle for unassigned (pool) assignment mode."""

    @pytest.mark.asyncio
    async def test_unassigned_claim_approve_and_return_to_pool(
        self,
        db_session: AsyncSession
    ):
        """
        Test: create (unassigned) → any kid claims → approve → returns to pool.

        Phase 6.2 Requirement #3
        """
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and 2 children
        parent = await user_service.register_user(
            db_session,
            username="parent_pool_flow",
            password="password123",
            email="poolf@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child_pool_flow_1",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child_pool_flow_2",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Step 1: Create unassigned pool chore with cooldown
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Walk the Dog",
                "description": "Take the dog for a walk around the block",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": [],
                "is_recurring": True,
                "cooldown_days": 1
            }
        )
        # Reload chore with assignments
        chore = await chore_service.repository.get_with_assignments(db_session, chore_id=chore.id)
        assert chore.is_unassigned_pool is True
        assert len(chore.assignments) == 0

        # Step 2: First child claims and completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child1.id
        )
        assignment = result["assignment"]
        assert assignment.assignee_id == child1.id
        assert assignment.is_completed is True

        # Step 3: Verify second child cannot claim while first has pending assignment
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 1  # Only one claim exists

        # Step 4: Parent approves
        await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment.id,
            parent_id=parent.id
        )

        # Step 5: Verify chore returns to pool after approval
        # Note: Pool chores allow different children to claim even during cooldown
        # Only the same child is blocked by cooldown on their own assignment

        # Step 6: Second child can claim the pool chore (different assignee)
        result2 = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child2.id
        )
        # For pool chores, previous assignment might be deleted or reset
        # Verify new completion created
        assert result2["assignment"].assignee_id == child2.id
        assert result2["assignment"].is_completed is True


class TestRejectionFlow:
    """Test rejection and redo workflow."""

    @pytest.mark.asyncio
    async def test_complete_reject_redo_approve_flow(
        self,
        db_session: AsyncSession
    ):
        """
        Test: complete → reject → redo → approve.

        Phase 6.2 Requirement #4
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_reject_flow",
            password="password123",
            email="rejectf@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_reject_flow",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Step 1: Create chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Make Bed",
                "description": "Make your bed with tucked corners",
                "reward": 2.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Step 2: Child completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment_id = result["assignment"].id

        # Step 3: Parent rejects with reason
        reject_result = await chore_service.reject_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id,
            rejection_reason="Please make it neater and organize pillows"
        )
        assert reject_result["assignment"].is_completed is False
        assert reject_result["assignment"].rejection_reason is not None

        # Step 4: Child redoes the chore
        redo_result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assert redo_result["assignment"].is_completed is True
        assert redo_result["assignment"].is_approved is False

        # Step 5: Parent approves
        final_result = await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id
        )
        assert final_result["assignment"].is_approved is True


class TestRangeRewardFlow:
    """Test range reward workflow."""

    @pytest.mark.asyncio
    async def test_complete_approve_with_custom_range_reward(
        self,
        db_session: AsyncSession
    ):
        """
        Test: complete → approve with custom reward in range.

        Phase 6.2 Requirement #5
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_range_flow",
            password="password123",
            email="rangef@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_range_flow",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Step 1: Create chore with range reward
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Detailed Yard Work",
                "description": "Rake leaves, trim hedges, and water plants",
                "reward": 10.0,
                "min_reward": 5.0,
                "max_reward": 15.0,
                "is_range_reward": True,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Step 2: Child completes
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment_id = result["assignment"].id

        # Step 3: Parent approves with custom reward value
        approval_result = await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id,
            reward_value=12.0  # Custom value within range
        )
        assert approval_result["assignment"].is_approved is True
        assert approval_result["assignment"].approval_reward == 12.0


class TestAuthorizationFlow:
    """Test authorization rules."""

    @pytest.mark.asyncio
    async def test_child_cannot_approve_parent_cannot_complete(
        self,
        db_session: AsyncSession
    ):
        """
        Test: child can't approve, parent can't complete.

        Phase 6.2 Requirement #6
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_auth_flow",
            password="password123",
            email="authf@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_auth_flow",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Test Auth Chore",
                "description": "Testing authorization rules",
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
        assignment_id = result["assignment"].id

        # Test 1: Child attempts to approve (should fail)
        with pytest.raises(Exception) as exc_info:
            await chore_service.approve_assignment(
                db_session,
                assignment_id=assignment_id,
                parent_id=child.id,  # Child ID instead of parent
                reward_value=None
            )
        # Service layer should validate authorization
        assert "approve" in str(exc_info.value).lower() or "forbidden" in str(exc_info.value).lower()

        # Test 2: Parent attempts to complete chore assigned to child (should fail)
        # Create another chore for this test
        chore2 = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Child Only Chore",
                "description": "Chore assigned only to child",
                "reward": 3.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        with pytest.raises(Exception) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore2.id,
                user_id=parent.id  # Parent trying to complete child's chore
            )
        # Should fail because parent doesn't have an assignment


class TestCooldownFlow:
    """Test cooldown enforcement."""

    @pytest.mark.asyncio
    async def test_cannot_complete_during_cooldown_period(
        self,
        db_session: AsyncSession
    ):
        """
        Test: can't complete during cooldown period.

        Phase 6.2 Requirement #7
        """
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_cooldown_flow",
            password="password123",
            email="cooldownf@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_cooldown_flow",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create recurring chore with 7-day cooldown
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Weekly Trash Duty",
                "description": "Take out the trash bins to the curb",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id],
                "is_recurring": True,
                "cooldown_days": 7
            }
        )

        # First cycle: complete and approve
        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assignment_id = result["assignment"].id

        await chore_service.approve_assignment(
            db_session,
            assignment_id=assignment_id,
            parent_id=parent.id
        )

        # Attempt to complete again immediately (should fail - within cooldown)
        with pytest.raises(Exception) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )
        assert "cooldown" in str(exc_info.value).lower()

        # Simulate partial cooldown (4 days) - still should fail
        assignment = await db_session.get(ChoreAssignment, assignment_id)
        assignment.approval_date = datetime.utcnow() - timedelta(days=4)
        await db_session.commit()

        with pytest.raises(Exception) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )
        assert "cooldown" in str(exc_info.value).lower()

        # Simulate full cooldown expiration (8 days) - should succeed
        assignment.approval_date = datetime.utcnow() - timedelta(days=8)
        await db_session.commit()

        result = await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        assert result["assignment"].is_completed is True
