"""Tests for enhanced ChoreService with V2 features."""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.chore_service_v2 import ChoreServiceV2
from backend.app.models.chore import Chore, RecurrenceType
from backend.app.models.user import User
from backend.app.models.chore_visibility import ChoreVisibility
from backend.app.schemas.chore import ChoreListResponse


@pytest.fixture
def chore_service_v2():
    """Create ChoreServiceV2 instance."""
    return ChoreServiceV2()


@pytest.fixture
async def parent_user(db_session: AsyncSession):
    """Create a parent user."""
    parent = User(
        username="parent@test.com",
        email="parent@test.com",
        hashed_password="hashed",
        is_parent=True
    )
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)
    return parent


@pytest.fixture
async def child_user(db_session: AsyncSession, parent_user: User):
    """Create a child user."""
    child = User(
        username="child@test.com",
        email="child@test.com",
        hashed_password="hashed",
        is_parent=False,
        parent_id=parent_user.id
    )
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)
    return child


@pytest.fixture
async def another_child_user(db_session: AsyncSession, parent_user: User):
    """Create another child user."""
    child = User(
        username="child2@test.com",
        email="child2@test.com",
        hashed_password="hashed",
        is_parent=False,
        parent_id=parent_user.id
    )
    db_session.add(child)
    await db_session.commit()
    await db_session.refresh(child)
    return child


@pytest.fixture
async def pool_chore(db_session: AsyncSession, parent_user: User):
    """Create an unassigned pool chore."""
    chore = Chore(
        title="Pool Chore",
        description="A chore in the master pool",
        reward=5.0,
        creator_id=parent_user.id,
        assignee_id=None,  # Unassigned
        is_recurring=True,
        recurrence_type=RecurrenceType.DAILY
    )
    db_session.add(chore)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


class TestChoreServiceV2:
    """Test cases for ChoreServiceV2."""
    
    async def test_get_pool_chores_as_parent(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        parent_user: User,
        pool_chore: Chore
    ):
        """Test parent sees all pool chores they created."""
        result = await chore_service_v2.get_pool_chores(db_session, user=parent_user)
        
        assert isinstance(result, ChoreListResponse)
        assert len(result.available_chores) == 1
        assert len(result.completed_chores) == 0
        assert result.available_chores[0].id == pool_chore.id
        assert result.available_chores[0].is_available is True
        assert result.available_chores[0].availability_progress == 100
    
    async def test_get_pool_chores_filters_hidden(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        parent_user: User,
        child_user: User,
        pool_chore: Chore
    ):
        """Test that hidden chores are excluded from child's pool view."""
        # Hide chore from child
        visibility = ChoreVisibility(
            chore_id=pool_chore.id,
            user_id=child_user.id,
            is_hidden=True
        )
        db_session.add(visibility)
        await db_session.commit()
        
        # Get pool chores as child
        result = await chore_service_v2.get_pool_chores(db_session, user=child_user)
        
        assert len(result.available_chores) == 0
        assert len(result.completed_chores) == 0
    
    async def test_get_pool_chores_with_recurrence(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test pool chores with recurrence show as unavailable after completion."""
        # Set last completion time to recent
        pool_chore.last_completion_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pool_chore.recurrence_type = RecurrenceType.DAILY
        await db_session.commit()
        
        # Get pool chores
        result = await chore_service_v2.get_pool_chores(db_session, user=child_user)
        
        # Should be in completed list, not available
        assert len(result.available_chores) == 0
        assert len(result.completed_chores) == 1
        assert result.completed_chores[0].id == pool_chore.id
        assert result.completed_chores[0].is_available is False
        assert result.completed_chores[0].availability_progress < 100
    
    async def test_claim_chore_success(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test successfully claiming an unassigned chore."""
        claimed_chore = await chore_service_v2.claim_chore(
            db_session,
            chore_id=pool_chore.id,
            user_id=child_user.id
        )
        
        assert claimed_chore.assignee_id == child_user.id
        assert claimed_chore.title == pool_chore.title
    
    async def test_claim_chore_already_assigned(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        another_child_user: User,
        pool_chore: Chore
    ):
        """Test claiming an already assigned chore fails."""
        # Assign chore to first child
        pool_chore.assignee_id = child_user.id
        await db_session.commit()
        
        # Try to claim as second child
        with pytest.raises(HTTPException) as exc_info:
            await chore_service_v2.claim_chore(
                db_session,
                chore_id=pool_chore.id,
                user_id=another_child_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "already assigned" in exc_info.value.detail
    
    async def test_claim_hidden_chore_fails(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        parent_user: User,
        child_user: User,
        pool_chore: Chore
    ):
        """Test claiming a hidden chore fails."""
        # Hide chore from child
        visibility = ChoreVisibility(
            chore_id=pool_chore.id,
            user_id=child_user.id,
            is_hidden=True
        )
        db_session.add(visibility)
        await db_session.commit()
        
        # Try to claim
        with pytest.raises(HTTPException) as exc_info:
            await chore_service_v2.claim_chore(
                db_session,
                chore_id=pool_chore.id,
                user_id=child_user.id
            )
        
        assert exc_info.value.status_code == 403
        assert "cannot claim this chore" in exc_info.value.detail
    
    async def test_claim_unavailable_chore_fails(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test claiming a chore in cooldown fails."""
        # Set recent completion
        pool_chore.last_completion_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pool_chore.recurrence_type = RecurrenceType.DAILY
        await db_session.commit()
        
        # Try to claim
        with pytest.raises(HTTPException) as exc_info:
            await chore_service_v2.claim_chore(
                db_session,
                chore_id=pool_chore.id,
                user_id=child_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "not yet available" in exc_info.value.detail
    
    async def test_complete_pool_chore_auto_claims(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test completing unassigned chore automatically claims it."""
        completed_chore = await chore_service_v2.complete_chore(
            db_session,
            chore_id=pool_chore.id,
            user_id=child_user.id
        )
        
        assert completed_chore.assignee_id == child_user.id
        assert completed_chore.is_completed is True
        assert completed_chore.last_completion_time is not None
    
    async def test_complete_chore_sets_next_available(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test that completing recurring chore sets next available time."""
        pool_chore.recurrence_type = RecurrenceType.DAILY
        pool_chore.assignee_id = child_user.id
        await db_session.commit()
        
        completed_chore = await chore_service_v2.complete_chore(
            db_session,
            chore_id=pool_chore.id,
            user_id=child_user.id
        )
        
        assert completed_chore.is_completed is True
        assert completed_chore.last_completion_time is not None
        assert completed_chore.next_available_time is not None
        
        # Next available should be tomorrow
        expected_next = completed_chore.last_completion_time + timedelta(days=1)
        assert completed_chore.next_available_time.date() == expected_next.date()
    
    async def test_cannot_complete_unavailable_chore(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test that unavailable chores cannot be completed."""
        # Set chore as completed recently
        pool_chore.assignee_id = child_user.id
        pool_chore.is_completed = True
        pool_chore.last_completion_time = datetime.now(timezone.utc) - timedelta(hours=1)
        pool_chore.recurrence_type = RecurrenceType.DAILY
        await db_session.commit()
        
        # Try to complete again
        with pytest.raises(HTTPException) as exc_info:
            await chore_service_v2.complete_chore(
                db_session,
                chore_id=pool_chore.id,
                user_id=child_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "not yet available" in exc_info.value.detail
    
    async def test_create_chore_with_visibility(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        parent_user: User,
        child_user: User,
        another_child_user: User
    ):
        """Test creating chore with visibility settings."""
        chore_data = {
            "title": "Visible to Some",
            "description": "This chore is hidden from one child",
            "reward": 10.0,
            "assignee_id": None  # Pool chore
        }
        
        chore = await chore_service_v2.create_chore_with_visibility(
            db_session,
            creator_id=parent_user.id,
            chore_data=chore_data,
            hidden_from_users=[child_user.id]
        )
        
        assert chore.id is not None
        
        # Verify visibility was set
        hidden_ids = await chore_service_v2.visibility_service.get_hidden_chore_ids_for_user(
            db_session, child_user.id
        )
        assert chore.id in hidden_ids
        
        # Verify not hidden from other child
        other_hidden_ids = await chore_service_v2.visibility_service.get_hidden_chore_ids_for_user(
            db_session, another_child_user.id
        )
        assert chore.id not in other_hidden_ids
    
    async def test_get_chore_with_availability(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test getting single chore with availability info."""
        # Set chore as recently completed
        pool_chore.last_completion_time = datetime.now(timezone.utc) - timedelta(hours=12)
        pool_chore.recurrence_type = RecurrenceType.DAILY
        await db_session.commit()
        
        chore_with_availability = await chore_service_v2.get_chore_with_availability(
            db_session,
            chore_id=pool_chore.id,
            user_id=child_user.id
        )
        
        assert chore_with_availability.id == pool_chore.id
        assert chore_with_availability.is_available is False
        assert 0 < chore_with_availability.availability_progress < 100
        assert chore_with_availability.is_hidden_from_current_user is False
    
    async def test_progress_calculation_accuracy(
        self,
        db_session: AsyncSession,
        chore_service_v2: ChoreServiceV2,
        child_user: User,
        pool_chore: Chore
    ):
        """Test that progress percentage is calculated correctly."""
        # Set completion at exactly 12 hours ago (50% through daily cycle)
        pool_chore.last_completion_time = datetime.now(timezone.utc) - timedelta(hours=12)
        pool_chore.recurrence_type = RecurrenceType.DAILY
        await db_session.commit()
        
        result = await chore_service_v2.get_pool_chores(db_session, user=child_user)
        
        assert len(result.completed_chores) == 1
        chore = result.completed_chores[0]
        
        # Progress should be around 50% (allowing for some timing variance)
        assert 45 <= chore.availability_progress <= 55