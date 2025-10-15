"""Unit tests for ChoreAssignment model and multi-assignment relationships."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.models.chore_assignment import ChoreAssignment
from backend.app.core.security.password import get_password_hash


@pytest_asyncio.fixture
async def parent_user(db_session):
    """Create a parent user for testing."""
    parent = User(
        email="test_parent@example.com",
        username="test_parent",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_parent=True
    )
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)
    return parent


@pytest_asyncio.fixture
async def child_users(db_session, parent_user):
    """Create multiple child users for testing."""
    children = []
    for i in range(3):
        child = User(
            email=f"child{i+1}@example.com",
            username=f"child_{i+1}",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=False,
            parent_id=parent_user.id
        )
        db_session.add(child)
        children.append(child)

    await db_session.commit()
    for child in children:
        await db_session.refresh(child)
    return children


@pytest_asyncio.fixture
async def single_assignment_chore(db_session, parent_user):
    """Create a single-assignment mode chore."""
    chore = Chore(
        title="Clean room",
        description="Vacuum and dust",
        reward=5.0,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        assignment_mode='single',
        creator_id=parent_user.id
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture
async def multi_independent_chore(db_session, parent_user):
    """Create a multi-independent assignment mode chore."""
    chore = Chore(
        title="Study for test",
        description="Review notes for math test",
        reward=10.0,
        is_range_reward=False,
        cooldown_days=7,
        is_recurring=True,
        assignment_mode='multi_independent',
        creator_id=parent_user.id
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture
async def unassigned_pool_chore(db_session, parent_user):
    """Create an unassigned pool mode chore."""
    chore = Chore(
        title="Take out trash",
        description="Empty trash cans",
        min_reward=2.0,
        max_reward=5.0,
        is_range_reward=True,
        cooldown_days=1,
        is_recurring=True,
        assignment_mode='unassigned',
        creator_id=parent_user.id
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


class TestChoreAssignmentModel:
    """Test ChoreAssignment model CRUD and properties."""

    async def test_create_assignment(self, db_session, single_assignment_chore, child_users):
        """Test creating a basic chore assignment."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        assert assignment.id is not None
        assert assignment.chore_id == single_assignment_chore.id
        assert assignment.assignee_id == child_users[0].id
        assert assignment.is_completed is False
        assert assignment.is_approved is False
        assert assignment.created_at is not None
        assert assignment.updated_at is not None

    async def test_unique_constraint(self, db_session, single_assignment_chore, child_users):
        """Test unique constraint on (chore_id, assignee_id)."""
        # Create first assignment
        assignment1 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment1)
        await db_session.commit()

        # Try to create duplicate assignment
        assignment2 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            await db_session.commit()

    async def test_assignment_completion_flow(self, db_session, single_assignment_chore, child_users):
        """Test assignment completion and approval workflow."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Mark as completed
        assignment.is_completed = True
        assignment.completion_date = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(assignment)

        assert assignment.is_completed is True
        assert assignment.completion_date is not None
        assert assignment.is_pending_approval is True

        # Approve the assignment
        assignment.is_approved = True
        assignment.approval_date = datetime.utcnow()
        assignment.approval_reward = 5.0
        await db_session.commit()
        await db_session.refresh(assignment)

        assert assignment.is_approved is True
        assert assignment.approval_date is not None
        assert assignment.approval_reward == 5.0
        assert assignment.is_pending_approval is False

    async def test_is_pending_approval_property(self, db_session, single_assignment_chore, child_users):
        """Test is_pending_approval property."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Not completed yet
        assert assignment.is_pending_approval is False

        # Completed but not approved
        assignment.is_completed = True
        assert assignment.is_pending_approval is True

        # Completed and approved
        assignment.is_approved = True
        assert assignment.is_pending_approval is False

    async def test_is_available_property_non_recurring(self, db_session, single_assignment_chore, child_users):
        """Test is_available property for non-recurring chore."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id,
            is_completed=False
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Available when not completed
        assert assignment.is_available is True

        # Not available when completed
        assignment.is_completed = True
        await db_session.commit()
        await db_session.refresh(assignment)
        assert assignment.is_available is False

    async def test_is_available_property_recurring_with_cooldown(self, db_session, multi_independent_chore, child_users):
        """Test is_available property for recurring chore with cooldown."""
        assignment = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[0].id,
            is_completed=False,
            is_approved=False
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Available initially
        assert assignment.is_available is True

        # Complete and approve (cooldown starts)
        assignment.is_completed = True
        assignment.is_approved = True
        assignment.approval_date = datetime.utcnow() - timedelta(days=3)  # 3 days ago
        await db_session.commit()
        await db_session.refresh(assignment)

        # Still in cooldown (7-day cooldown, only 3 days passed)
        # But is_available checks is_completed first, so it's False
        assert assignment.is_available is False

        # Reset completion to test cooldown logic
        assignment.is_completed = False
        await db_session.commit()
        await db_session.refresh(assignment)

        # Now check if cooldown passed (it hasn't - 3 days < 7 days)
        assert assignment.is_available is False

        # Set approval_date to 8 days ago (cooldown passed)
        assignment.approval_date = datetime.utcnow() - timedelta(days=8)
        await db_session.commit()
        await db_session.refresh(assignment)
        assert assignment.is_available is True

    async def test_days_until_available_property(self, db_session, multi_independent_chore, child_users):
        """Test days_until_available property calculation."""
        assignment = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[0].id,
            is_completed=False,
            is_approved=True,
            approval_date=datetime.utcnow() - timedelta(days=3)  # 3 days ago
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Chore has 7-day cooldown, 3 days have passed, so 4 days remaining
        days_left = assignment.days_until_available
        assert days_left is not None
        assert 3 <= days_left <= 4  # Allow for test execution time

        # Set approval_date to 8 days ago (cooldown passed)
        assignment.approval_date = datetime.utcnow() - timedelta(days=8)
        await db_session.commit()
        await db_session.refresh(assignment)
        assert assignment.days_until_available == 0

    async def test_rejection_reason(self, db_session, single_assignment_chore, child_users):
        """Test rejection reason field."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id,
            is_completed=True,
            is_approved=False,
            rejection_reason="Not thorough enough"
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        assert assignment.rejection_reason == "Not thorough enough"
        assert assignment.is_approved is False


class TestChoreModelRelationships:
    """Test Chore model relationships with ChoreAssignment."""

    async def test_chore_assignments_relationship(self, db_session, single_assignment_chore, child_users):
        """Test chore.assignments relationship."""
        # Create assignments
        assignment1 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        assignment2 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[1].id
        )
        db_session.add_all([assignment1, assignment2])
        await db_session.commit()

        # Fetch chore with assignments
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == single_assignment_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert len(chore.assignments) == 2
        assert assignment1 in chore.assignments
        assert assignment2 in chore.assignments

    async def test_chore_assignment_mode_properties(self, db_session, single_assignment_chore, multi_independent_chore, unassigned_pool_chore):
        """Test chore assignment mode properties."""
        # Single assignment mode
        assert single_assignment_chore.is_single_assignment is True
        assert single_assignment_chore.is_multi_independent is False
        assert single_assignment_chore.is_unassigned_pool is False

        # Multi-independent mode
        assert multi_independent_chore.is_single_assignment is False
        assert multi_independent_chore.is_multi_independent is True
        assert multi_independent_chore.is_unassigned_pool is False

        # Unassigned pool mode
        assert unassigned_pool_chore.is_single_assignment is False
        assert unassigned_pool_chore.is_multi_independent is False
        assert unassigned_pool_chore.is_unassigned_pool is True

    async def test_chore_has_assignments_property(self, db_session, single_assignment_chore, child_users):
        """Test chore.has_assignments property."""
        # Fetch chore with assignments loaded
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == single_assignment_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        # Initially no assignments
        assert chore.has_assignments is False

        # Add assignment
        assignment = ChoreAssignment(
            chore_id=chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Refresh chore with assignments - need to get fresh instance from DB
        chore_id = chore.id  # Store ID before expiring
        db_session.expire(chore)  # expire() is synchronous, not async
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == chore_id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert chore.has_assignments is True

    async def test_chore_pending_approval_count(self, db_session, multi_independent_chore, child_users):
        """Test chore.pending_approval_count property."""
        # Create multiple assignments in different states
        assignment1 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[0].id,
            is_completed=True,  # Pending approval
            is_approved=False
        )
        assignment2 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[1].id,
            is_completed=True,  # Pending approval
            is_approved=False
        )
        assignment3 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[2].id,
            is_completed=True,  # Approved
            is_approved=True
        )
        db_session.add_all([assignment1, assignment2, assignment3])
        await db_session.commit()

        # Fetch chore with assignments
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == multi_independent_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert chore.pending_approval_count == 2

    async def test_chore_approved_count(self, db_session, multi_independent_chore, child_users):
        """Test chore.approved_count property."""
        # Create assignments with different approval states
        assignment1 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[0].id,
            is_completed=True,
            is_approved=True
        )
        assignment2 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[1].id,
            is_completed=True,
            is_approved=False
        )
        assignment3 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[2].id,
            is_completed=False,
            is_approved=False
        )
        db_session.add_all([assignment1, assignment2, assignment3])
        await db_session.commit()

        # Fetch chore with assignments
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == multi_independent_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert chore.approved_count == 1


class TestUserModelRelationships:
    """Test User model relationships with ChoreAssignment."""

    async def test_user_chore_assignments_relationship(self, db_session, child_users, single_assignment_chore, multi_independent_chore):
        """Test user.chore_assignments relationship."""
        # Create assignments for child
        assignment1 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        assignment2 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add_all([assignment1, assignment2])
        await db_session.commit()

        # Fetch user with assignments
        result = await db_session.execute(
            select(User)
            .where(User.id == child_users[0].id)
            .options(selectinload(User.chore_assignments))
        )
        user = result.scalar_one()

        assert len(user.chore_assignments) == 2
        assert assignment1 in user.chore_assignments
        assert assignment2 in user.chore_assignments

    async def test_assignment_assignee_relationship(self, db_session, single_assignment_chore, child_users):
        """Test assignment.assignee relationship."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment)
        await db_session.commit()

        # Fetch assignment with assignee loaded
        result = await db_session.execute(
            select(ChoreAssignment)
            .where(ChoreAssignment.id == assignment.id)
            .options(selectinload(ChoreAssignment.assignee))
        )
        loaded_assignment = result.scalar_one()

        assert loaded_assignment.assignee is not None
        assert loaded_assignment.assignee.id == child_users[0].id
        assert loaded_assignment.assignee.username == child_users[0].username


class TestCascadeDelete:
    """Test CASCADE delete behavior."""

    async def test_delete_chore_cascades_to_assignments(self, db_session, single_assignment_chore, child_users):
        """Test that deleting a chore deletes its assignments."""
        # Create assignments
        assignment1 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        assignment2 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[1].id
        )
        db_session.add_all([assignment1, assignment2])
        await db_session.commit()

        assignment_ids = [assignment1.id, assignment2.id]

        # Delete the chore
        await db_session.delete(single_assignment_chore)
        await db_session.commit()

        # Verify assignments are deleted
        result = await db_session.execute(
            select(ChoreAssignment).where(ChoreAssignment.id.in_(assignment_ids))
        )
        remaining_assignments = result.scalars().all()

        assert len(remaining_assignments) == 0

    async def test_delete_user_cascades_to_assignments(self, db_session, single_assignment_chore, multi_independent_chore, child_users):
        """Test that deleting a user deletes their assignments."""
        # Create assignments for a child
        assignment1 = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        assignment2 = ChoreAssignment(
            chore_id=multi_independent_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add_all([assignment1, assignment2])
        await db_session.commit()

        assignment_ids = [assignment1.id, assignment2.id]
        user_id = child_users[0].id

        # Delete the user
        await db_session.delete(child_users[0])
        await db_session.commit()

        # Verify assignments are deleted
        result = await db_session.execute(
            select(ChoreAssignment).where(ChoreAssignment.id.in_(assignment_ids))
        )
        remaining_assignments = result.scalars().all()

        assert len(remaining_assignments) == 0

        # Verify user is deleted
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        assert user is None


class TestMultiAssignmentScenarios:
    """Test real-world multi-assignment scenarios."""

    async def test_single_assignment_mode_one_child(self, db_session, single_assignment_chore, child_users):
        """Test single assignment mode with one child assigned."""
        assignment = ChoreAssignment(
            chore_id=single_assignment_chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment)
        await db_session.commit()

        # Fetch chore with assignments
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == single_assignment_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert chore.is_single_assignment is True
        assert len(chore.assignments) == 1
        assert chore.has_assignments is True

    async def test_multi_independent_mode_multiple_children(self, db_session, multi_independent_chore, child_users):
        """Test multi-independent mode with multiple children."""
        # Assign to all 3 children
        assignments = [
            ChoreAssignment(
                chore_id=multi_independent_chore.id,
                assignee_id=child.id
            )
            for child in child_users
        ]
        db_session.add_all(assignments)
        await db_session.commit()

        # Fetch chore with assignments
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == multi_independent_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert chore.is_multi_independent is True
        assert len(chore.assignments) == 3

        # Each child completes independently
        assignments[0].is_completed = True
        assignments[0].completion_date = datetime.utcnow()
        await db_session.commit()

        # Refresh all assignments to get current state
        for assignment in assignments:
            await db_session.refresh(assignment)

        # Other assignments still not completed
        assert assignments[1].is_completed is False
        assert assignments[2].is_completed is False

    async def test_unassigned_pool_dynamic_claiming(self, db_session, unassigned_pool_chore, child_users):
        """Test unassigned pool mode where children claim chores."""
        # Fetch chore
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == unassigned_pool_chore.id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        # Initially no assignments
        assert chore.is_unassigned_pool is True
        assert len(chore.assignments) == 0

        # Child 1 claims the chore
        assignment = ChoreAssignment(
            chore_id=chore.id,
            assignee_id=child_users[0].id
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)

        # Refresh chore - get fresh instance from DB
        chore_id = chore.id  # Store ID before expiring
        db_session.expire(chore)
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == chore_id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert len(chore.assignments) == 1

        # After approval and cooldown, another child can claim
        assignment.is_completed = True
        assignment.is_approved = True
        assignment.approval_date = datetime.utcnow() - timedelta(days=2)  # Cooldown is 1 day
        await db_session.commit()
        await db_session.refresh(assignment)

        # Child 2 claims it (creating a new assignment)
        chore_id = chore.id  # Store ID again
        assignment2 = ChoreAssignment(
            chore_id=chore_id,
            assignee_id=child_users[1].id
        )
        db_session.add(assignment2)
        await db_session.commit()
        await db_session.refresh(assignment2)

        # Refresh chore - get fresh instance from DB
        db_session.expire(chore)
        result = await db_session.execute(
            select(Chore)
            .where(Chore.id == chore_id)
            .options(selectinload(Chore.assignments))
        )
        chore = result.scalar_one()

        assert len(chore.assignments) == 2
