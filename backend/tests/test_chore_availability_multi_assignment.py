"""
Test ChoreService availability queries for multi-assignment chores.

Tests the availability logic for all three assignment modes:
- get_available_chores(): Returns assigned + pool chores for child
- get_pending_approval(): Returns assignment-level data for parent
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.repositories.chore_assignment import ChoreAssignmentRepository


class TestChoreAvailabilityMultiAssignment:
    """Test multi-assignment chore availability queries."""

    @pytest.mark.asyncio
    async def test_get_available_assigned_chores(self, db_session: AsyncSession):
        """Test that child sees their assigned chores (not completed, outside cooldown)."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_avail_assigned",
            password="password123",
            email="parentaa@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_avail_assigned",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create 3 chores: 1 available, 1 completed, 1 disabled
        chore1 = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Available Chore",
                "description": "Not started",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        chore2 = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Completed Chore",
                "description": "Already done",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete chore2
        await chore_service.complete_chore(db_session, chore_id=chore2.id, user_id=child.id)

        chore3 = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Disabled Chore",
                "description": "Not active",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Disable chore3
        await chore_service.disable_chore(db_session, chore_id=chore3.id, parent_id=parent.id)

        # Get available chores
        result = await chore_service.get_available_chores(db_session, child_id=child.id)

        # Should only see chore1
        assert len(result["assigned"]) == 1
        assert result["assigned"][0]["chore"].id == chore1.id
        assert result["assigned"][0]["assignment"] is not None
        assert len(result["pool"]) == 0

    @pytest.mark.asyncio
    async def test_get_available_pool_chores(self, db_session: AsyncSession):
        """Test that child sees unassigned pool chores."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_avail_pool",
            password="password123",
            email="parentap@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_avail_pool",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create 2 pool chores
        pool1 = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Walk the Dog",
                "description": "Anyone can do",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []
            }
        )

        pool2 = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Water Plants",
                "description": "Anyone can do",
                "reward": 2.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []
            }
        )

        # Get available chores
        result = await chore_service.get_available_chores(db_session, child_id=child.id)

        # Should see both pool chores
        assert len(result["assigned"]) == 0
        assert len(result["pool"]) == 2
        pool_ids = {c["chore"].id for c in result["pool"]}
        assert pool1.id in pool_ids
        assert pool2.id in pool_ids

    @pytest.mark.asyncio
    async def test_get_available_excludes_claimed_pool_chores(self, db_session: AsyncSession):
        """Test that child doesn't see pool chores they already claimed."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_claimed",
            password="password123",
            email="parentclaimed@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_claimed",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create pool chore
        pool_chore = await chore_service.create_chore(
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
        await chore_service.complete_chore(db_session, chore_id=pool_chore.id, user_id=child.id)

        # Get available chores
        result = await chore_service.get_available_chores(db_session, child_id=child.id)

        # Should NOT see the pool chore (already claimed)
        assert len(result["pool"]) == 0
        assert len(result["assigned"]) == 0  # Completed, so not in assigned either

    @pytest.mark.asyncio
    async def test_get_available_multi_independent(self, db_session: AsyncSession):
        """Test multi-independent mode: each child sees their own assignment."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and 3 children
        parent = await user_service.register_user(
            db_session,
            username="parent_multi_avail",
            password="password123",
            email="parentma@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_multi_avail",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_multi_avail",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_multi_avail",
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
                "description": "Each child's room",
                "reward": 10.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id, child3.id]
            }
        )

        # Each child should see the chore
        result1 = await chore_service.get_available_chores(db_session, child_id=child1.id)
        result2 = await chore_service.get_available_chores(db_session, child_id=child2.id)
        result3 = await chore_service.get_available_chores(db_session, child_id=child3.id)

        assert len(result1["assigned"]) == 1
        assert len(result2["assigned"]) == 1
        assert len(result3["assigned"]) == 1

        # Child1 completes their assignment
        await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child1.id)

        # Child1 should no longer see it (completed)
        result1_after = await chore_service.get_available_chores(db_session, child_id=child1.id)
        assert len(result1_after["assigned"]) == 0

        # But child2 and child3 should still see it
        result2_after = await chore_service.get_available_chores(db_session, child_id=child2.id)
        result3_after = await chore_service.get_available_chores(db_session, child_id=child3.id)

        assert len(result2_after["assigned"]) == 1
        assert len(result3_after["assigned"]) == 1

    @pytest.mark.asyncio
    async def test_get_available_cooldown_exclusion(self, db_session: AsyncSession):
        """Test that chores in cooldown are not shown as available."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_cooldown_avail",
            password="password123",
            email="parentca@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_cooldown_avail",
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
                "description": "Once a week",
                "reward": 10.0,
                "is_recurring": True,
                "cooldown_days": 7,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Complete and approve
        result = await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child.id)
        assignment = result["assignment"]

        # Manually set approval (simulate recent approval)
        await assignment_repo.update(
            db_session,
            id=assignment.id,
            obj_in={
                "is_approved": True,
                "approval_date": datetime.utcnow() - timedelta(days=3)  # 3 days ago
            }
        )

        # Get available chores - should NOT see it (still in cooldown)
        avail_result = await chore_service.get_available_chores(db_session, child_id=child.id)
        assert len(avail_result["assigned"]) == 0

    @pytest.mark.asyncio
    async def test_get_pending_approval_single_mode(self, db_session: AsyncSession):
        """Test parent sees pending approval with assignment details."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_pending",
            password="password123",
            email="parentpending@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_pending",
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
                "description": "Pending",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child.id)

        # Get pending approvals
        pending = await chore_service.get_pending_approval(db_session, parent_id=parent.id)

        # Should see 1 pending assignment
        assert len(pending) == 1
        assert pending[0]["chore"].id == chore.id
        assert pending[0]["assignee"].id == child.id
        assert pending[0]["assignee_name"] == child.username
        assert pending[0]["assignment"].is_completed is True
        assert pending[0]["assignment"].is_approved is False

    @pytest.mark.asyncio
    async def test_get_pending_approval_multi_independent(self, db_session: AsyncSession):
        """Test parent sees multiple pending assignments for multi-independent chore."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and 3 children
        parent = await user_service.register_user(
            db_session,
            username="parent_pending_multi",
            password="password123",
            email="parentpm@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_pending_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_pending_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_pending_multi",
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
                "description": "Multi-independent",
                "reward": 10.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id, child3.id]
            }
        )

        # All 3 children complete
        await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child1.id)
        await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child2.id)
        await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child3.id)

        # Get pending approvals
        pending = await chore_service.get_pending_approval(db_session, parent_id=parent.id)

        # Should see 3 separate assignments
        assert len(pending) == 3

        assignee_ids = {p["assignee"].id for p in pending}
        assert child1.id in assignee_ids
        assert child2.id in assignee_ids
        assert child3.id in assignee_ids

        # All should be for the same chore
        assert all(p["chore"].id == chore.id for p in pending)

    @pytest.mark.asyncio
    async def test_get_pending_approval_excludes_approved(self, db_session: AsyncSession):
        """Test that approved assignments are not in pending list."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and 2 children
        parent = await user_service.register_user(
            db_session,
            username="parent_excl_approved",
            password="password123",
            email="parentea@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_excl_approved",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_excl_approved",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create multi-independent chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Test Chore",
                "description": "Multi",
                "reward": 5.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id]
            }
        )

        # Both complete
        result1 = await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child1.id)
        result2 = await chore_service.complete_chore(db_session, chore_id=chore.id, user_id=child2.id)

        # Approve child1's assignment
        await chore_service.approve_assignment(
            db_session,
            assignment_id=result1["assignment"].id,
            parent_id=parent.id
        )

        # Get pending approvals
        pending = await chore_service.get_pending_approval(db_session, parent_id=parent.id)

        # Should only see child2's assignment
        assert len(pending) == 1
        assert pending[0]["assignee"].id == child2.id
