"""
Test ChoreService multi-assignment functionality.

Tests the new multi-assignment chore creation with three modes:
- single: One assignee per chore
- multi_independent: Multiple assignees, each with independent completion
- unassigned: Pool chores that any child can claim
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.repositories.chore_assignment import ChoreAssignmentRepository


class TestChoreServiceMultiAssignment:
    """Test multi-assignment chore creation business logic."""

    @pytest.mark.asyncio
    async def test_create_single_mode_chore(self, db_session: AsyncSession):
        """Test creating a chore with single assignment mode."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_single",
            password="password123",
            email="parentsingle@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_single",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with single assignment mode
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Single Mode Chore",
                "description": "Test single assignment",
                "reward": 5.0,
                "assignment_mode": "single",
                "assignee_ids": [child.id]
            }
        )

        # Verify chore was created
        assert chore is not None
        assert chore.title == "Single Mode Chore"
        assert chore.assignment_mode == "single"
        assert chore.creator_id == parent.id

        # Verify assignment was created
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 1
        assert assignments[0].assignee_id == child.id
        assert assignments[0].is_completed is False
        assert assignments[0].is_approved is False

    @pytest.mark.asyncio
    async def test_create_multi_independent_mode_chore(self, db_session: AsyncSession):
        """Test creating a chore with multi_independent assignment mode."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and three children
        parent = await user_service.register_user(
            db_session,
            username="parent_multi",
            password="password123",
            email="parentmulti@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child3 = await user_service.register_user(
            db_session,
            username="child3_multi",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with multi_independent assignment mode
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Multi-Independent Chore",
                "description": "Test multi-independent assignment",
                "reward": 10.0,
                "is_recurring": True,
                "cooldown_days": 7,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id, child3.id]
            }
        )

        # Verify chore was created
        assert chore is not None
        assert chore.title == "Multi-Independent Chore"
        assert chore.assignment_mode == "multi_independent"
        assert chore.is_recurring is True

        # Verify 3 assignments were created
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 3

        assignee_ids = {a.assignee_id for a in assignments}
        assert assignee_ids == {child1.id, child2.id, child3.id}

        # All assignments should be in pending state
        for assignment in assignments:
            assert assignment.is_completed is False
            assert assignment.is_approved is False

    @pytest.mark.asyncio
    async def test_create_unassigned_mode_chore(self, db_session: AsyncSession):
        """Test creating an unassigned pool chore."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_unassigned",
            password="password123",
            email="parentunassigned@test.com",
            is_parent=True
        )

        # Create chore with unassigned mode (pool chore)
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Unassigned Pool Chore",
                "description": "Any child can claim this",
                "reward": 3.0,
                "assignment_mode": "unassigned",
                "assignee_ids": []  # Empty list for unassigned
            }
        )

        # Verify chore was created
        assert chore is not None
        assert chore.title == "Unassigned Pool Chore"
        assert chore.assignment_mode == "unassigned"

        # Verify NO assignments were created
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 0

    @pytest.mark.asyncio
    async def test_create_single_mode_with_wrong_count(self, db_session: AsyncSession):
        """Test that single mode requires exactly 1 assignee."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and two children
        parent = await user_service.register_user(
            db_session,
            username="parent_single_wrong",
            password="password123",
            email="parentsw@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_sw",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_sw",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Try to create single mode with 2 assignees (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Wrong Count",
                    "description": "Test",
                    "reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": [child1.id, child2.id]  # Too many!
                }
            )

        assert exc_info.value.status_code == 422
        assert "'single' assignment mode requires exactly 1 assignee_id" in str(exc_info.value.detail)

        # Try to create single mode with 0 assignees (should also fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "No Assignees",
                    "description": "Test",
                    "reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": []  # Too few!
                }
            )

        assert exc_info.value.status_code == 422
        assert "'single' assignment mode requires exactly 1 assignee_id" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_multi_mode_with_zero_assignees(self, db_session: AsyncSession):
        """Test that multi_independent mode requires at least 1 assignee."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_multi_zero",
            password="password123",
            email="parentmz@test.com",
            is_parent=True
        )

        # Try to create multi_independent mode with 0 assignees (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "No Assignees Multi",
                    "description": "Test",
                    "reward": 5.0,
                    "assignment_mode": "multi_independent",
                    "assignee_ids": []  # Empty!
                }
            )

        assert exc_info.value.status_code == 422
        assert "'multi_independent' assignment mode requires at least 1 assignee_id" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_unassigned_mode_with_assignees(self, db_session: AsyncSession):
        """Test that unassigned mode must have 0 assignees."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_unassign_wrong",
            password="password123",
            email="parentuw@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_uw",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Try to create unassigned mode with assignees (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Unassigned with Assignees",
                    "description": "Test",
                    "reward": 5.0,
                    "assignment_mode": "unassigned",
                    "assignee_ids": [child.id]  # Should be empty!
                }
            )

        assert exc_info.value.status_code == 422
        assert "'unassigned' assignment mode must have 0 assignee_ids" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_chore_with_nonexistent_assignee(self, db_session: AsyncSession):
        """Test creating chore with non-existent assignee ID."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_nonexist",
            password="password123",
            email="parentne@test.com",
            is_parent=True
        )

        # Try to create chore with non-existent assignee
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Bad Assignee",
                    "description": "Test",
                    "reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": [99999]  # Doesn't exist
                }
            )

        assert exc_info.value.status_code == 404
        assert "Assignee with ID 99999 not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_chore_assignee_from_different_parent(self, db_session: AsyncSession):
        """Test that parent cannot assign chore to another parent's child."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_diffparent",
            password="password123",
            email="parent1dp@test.com",
            is_parent=True
        )

        parent2 = await user_service.register_user(
            db_session,
            username="parent2_diffparent",
            password="password123",
            email="parent2dp@test.com",
            is_parent=True
        )

        # Create child for parent2
        child_of_parent2 = await user_service.register_user(
            db_session,
            username="child_p2",
            password="password123",
            is_parent=False,
            parent_id=parent2.id
        )

        # Parent1 tries to assign chore to parent2's child
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent1.id,
                chore_data={
                    "title": "Cross-Parent Chore",
                    "description": "Test",
                    "reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": [child_of_parent2.id]
                }
            )

        assert exc_info.value.status_code == 403
        assert "is not your child" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_multi_chore_with_range_reward(self, db_session: AsyncSession):
        """Test creating multi-assignment chore with range reward."""
        user_service = UserService()
        chore_service = ChoreService()
        assignment_repo = ChoreAssignmentRepository()

        # Create parent and two children
        parent = await user_service.register_user(
            db_session,
            username="parent_range_multi",
            password="password123",
            email="parentrm@test.com",
            is_parent=True
        )

        child1 = await user_service.register_user(
            db_session,
            username="child1_rm",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        child2 = await user_service.register_user(
            db_session,
            username="child2_rm",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Create chore with range reward and multi_independent mode
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Range Reward Multi Chore",
                "description": "Parent sets reward on approval",
                "is_range_reward": True,
                "min_reward": 3.0,
                "max_reward": 10.0,
                "assignment_mode": "multi_independent",
                "assignee_ids": [child1.id, child2.id]
            }
        )

        # Verify chore was created
        assert chore is not None
        assert chore.is_range_reward is True
        assert chore.min_reward == 3.0
        assert chore.max_reward == 10.0

        # Verify both assignments were created
        assignments = await assignment_repo.get_by_chore(db_session, chore_id=chore.id)
        assert len(assignments) == 2

    @pytest.mark.asyncio
    async def test_create_chore_invalid_range_reward(self, db_session: AsyncSession):
        """Test that min_reward must be less than max_reward."""
        user_service = UserService()
        chore_service = ChoreService()

        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_invalid_range",
            password="password123",
            email="parentir@test.com",
            is_parent=True
        )

        child = await user_service.register_user(
            db_session,
            username="child_ir",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )

        # Try to create chore with invalid range (min > max)
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Invalid Range",
                    "description": "Test",
                    "is_range_reward": True,
                    "min_reward": 10.0,  # Greater than max!
                    "max_reward": 5.0,
                    "assignment_mode": "single",
                    "assignee_ids": [child.id]
                }
            )

        assert exc_info.value.status_code == 422
        assert "Minimum reward must be less than maximum reward" in str(exc_info.value.detail)
