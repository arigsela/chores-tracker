"""
Comprehensive tests for repository layer.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.user import UserRepository
from backend.app.repositories.chore import ChoreRepository
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import verify_password


class TestUserRepository:
    """Test UserRepository methods."""
    
    @pytest_asyncio.fixture
    async def user_repo(self):
        """Create a UserRepository instance."""
        return UserRepository()
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test creating a new user."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "is_parent": True
        }
        
        user = await user_repo.create(db_session, obj_in=user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_parent is True
        assert user.is_active is True
        assert verify_password("testpass123", user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_create_child_user(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test creating a child user with parent."""
        child_data = {
            "username": "childuser",
            "email": "child@example.com",
            "password": "childpass123",
            "is_parent": False,
            "parent_id": test_parent_user.id
        }
        
        child = await user_repo.create(db_session, obj_in=child_data)
        
        assert child.username == "childuser"
        assert child.is_parent is False
        assert child.parent_id == test_parent_user.id
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test getting user by email."""
        user = await user_repo.get_by_email(db_session, email=test_parent_user.email)
        assert user is not None
        assert user.id == test_parent_user.id
        assert user.email == test_parent_user.email
    
    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test getting non-existent user by email."""
        user = await user_repo.get_by_email(db_session, email="nonexistent@example.com")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_by_username(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test getting user by username."""
        user = await user_repo.get_by_username(db_session, username=test_parent_user.username)
        assert user is not None
        assert user.id == test_parent_user.id
        assert user.username == test_parent_user.username
    
    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test getting non-existent user by username."""
        user = await user_repo.get_by_username(db_session, username="nonexistentuser")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test successful authentication."""
        # Create a user with known password
        user_data = {
            "username": "authuser",
            "email": "auth@example.com",
            "password": "authpass123",
            "is_parent": True
        }
        created_user = await user_repo.create(db_session, obj_in=user_data)
        
        # Test authentication
        authenticated_user = await user_repo.authenticate(
            db_session, 
            username="authuser", 
            password="authpass123"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.username == "authuser"
    
    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test authentication with wrong password."""
        # Create a user
        user_data = {
            "username": "authuser2",
            "email": "auth2@example.com",
            "password": "correctpass",
            "is_parent": True
        }
        await user_repo.create(db_session, obj_in=user_data)
        
        # Test authentication with wrong password
        authenticated_user = await user_repo.authenticate(
            db_session, 
            username="authuser2", 
            password="wrongpass"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test authentication with non-existent user."""
        authenticated_user = await user_repo.authenticate(
            db_session, 
            username="nonexistent", 
            password="anypass"
        )
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_get_children(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test getting children for a parent."""
        # Create multiple children
        for i in range(3):
            child_data = {
                "username": f"child{i}",
                "email": f"child{i}@example.com",
                "password": "childpass",
                "is_parent": False,
                "parent_id": test_parent_user.id
            }
            await user_repo.create(db_session, obj_in=child_data)
        
        # Get children
        children = await user_repo.get_children(db_session, parent_id=test_parent_user.id)
        
        assert len(children) == 3
        assert all(child.parent_id == test_parent_user.id for child in children)
        assert all(child.is_parent is False for child in children)
    
    @pytest.mark.asyncio
    async def test_get_children_empty(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test getting children when parent has none."""
        children = await user_repo.get_children(db_session, parent_id=test_parent_user.id)
        assert children == []
    
    @pytest.mark.asyncio
    async def test_reset_password(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test resetting user password."""
        new_password = "newpass123"
        
        updated_user = await user_repo.reset_password(
            db_session, 
            user_id=test_parent_user.id, 
            new_password=new_password
        )
        
        assert updated_user is not None
        assert updated_user.id == test_parent_user.id
        assert verify_password(new_password, updated_user.hashed_password)
        
        # Verify authentication with new password
        authenticated = await user_repo.authenticate(
            db_session,
            username=test_parent_user.username,
            password=new_password
        )
        assert authenticated is not None
    
    @pytest.mark.asyncio
    async def test_reset_password_short(self, db_session: AsyncSession, user_repo: UserRepository, test_parent_user: User):
        """Test resetting password with too short password."""
        with pytest.raises(ValueError, match="Password must be at least 4 characters long"):
            await user_repo.reset_password(
                db_session, 
                user_id=test_parent_user.id, 
                new_password="abc"
            )
    
    @pytest.mark.asyncio
    async def test_reset_password_nonexistent_user(self, db_session: AsyncSession, user_repo: UserRepository):
        """Test resetting password for non-existent user."""
        updated_user = await user_repo.reset_password(
            db_session, 
            user_id=99999, 
            new_password="newpass123"
        )
        
        assert updated_user is None


class TestChoreRepository:
    """Test ChoreRepository methods."""
    
    @pytest_asyncio.fixture
    async def chore_repo(self):
        """Create a ChoreRepository instance."""
        return ChoreRepository()
    
    @pytest.mark.asyncio
    async def test_get_available_for_assignee(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test getting available chores for a child."""
        # Create multiple chores
        chores_data = [
            {
                "title": "Available Chore 1",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": False,
                "is_disabled": False
            },
            {
                "title": "Completed Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": True,
                "is_disabled": False
            },
            {
                "title": "Disabled Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": False,
                "is_disabled": True
            },
            {
                "title": "Available Chore 2",
                "description": "Test",
                "reward": 10.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": False,
                "is_disabled": False
            }
        ]
        
        for chore_data in chores_data:
            chore = Chore(**chore_data)
            db_session.add(chore)
        await db_session.commit()
        
        # Get available chores
        available_chores = await chore_repo.get_available_for_assignee(
            db_session, 
            assignee_id=test_child_user.id
        )
        
        assert len(available_chores) == 2
        assert all(not chore.is_completed for chore in available_chores)
        assert all(not chore.is_disabled for chore in available_chores)
        assert all(chore.assignee_id == test_child_user.id for chore in available_chores)
    
    @pytest.mark.asyncio
    async def test_get_pending_approval(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test getting chores pending approval."""
        # Create chores with different states
        chores_data = [
            {
                "title": "Pending Approval 1",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": True,
                "is_approved": False,
                "is_disabled": False
            },
            {
                "title": "Already Approved",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": True,
                "is_approved": True,
                "is_disabled": False
            },
            {
                "title": "Not Completed",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": False,
                "is_approved": False,
                "is_disabled": False
            },
            {
                "title": "Pending Approval 2",
                "description": "Test",
                "reward": 10.0,
                "assignee_id": test_child_user.id,
                "creator_id": test_parent_user.id,
                "is_completed": True,
                "is_approved": False,
                "is_disabled": False
            }
        ]
        
        for chore_data in chores_data:
            chore = Chore(**chore_data)
            db_session.add(chore)
        await db_session.commit()
        
        # Get pending approval chores
        pending_chores = await chore_repo.get_pending_approval(
            db_session, 
            creator_id=test_parent_user.id
        )
        
        assert len(pending_chores) == 2
        assert all(chore.is_completed for chore in pending_chores)
        assert all(not chore.is_approved for chore in pending_chores)
        assert all(chore.creator_id == test_parent_user.id for chore in pending_chores)
    
    @pytest.mark.asyncio
    async def test_mark_completed(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_chore: Chore
    ):
        """Test completing a chore."""
        assert test_chore.is_completed is False
        
        completed_chore = await chore_repo.mark_completed(
            db_session, 
            chore_id=test_chore.id
        )
        
        assert completed_chore is not None
        assert completed_chore.is_completed is True
        assert completed_chore.completion_date is not None
    
    @pytest.mark.asyncio
    async def test_mark_completed_nonexistent(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository
    ):
        """Test completing non-existent chore."""
        completed_chore = await chore_repo.mark_completed(
            db_session, 
            chore_id=99999
        )
        
        assert completed_chore is None
    
    @pytest.mark.asyncio
    async def test_approve_chore_fixed_reward(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_chore: Chore
    ):
        """Test approving a chore with fixed reward."""
        # First complete the chore
        await chore_repo.mark_completed(db_session, chore_id=test_chore.id)
        
        # Then approve it
        approved_chore = await chore_repo.approve_chore(
            db_session, 
            chore_id=test_chore.id,
            reward_value=None  # Fixed reward doesn't need value
        )
        
        assert approved_chore is not None
        assert approved_chore.is_approved is True
        assert approved_chore.reward == test_chore.reward
    
    @pytest.mark.asyncio
    async def test_approve_chore_range_reward(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_range_chore: Chore
    ):
        """Test approving a chore with range reward."""
        # First complete the chore
        await chore_repo.mark_completed(db_session, chore_id=test_range_chore.id)
        
        # Then approve it with specific reward
        reward_value = 3.0  # Between min (2.0) and max (4.0)
        approved_chore = await chore_repo.approve_chore(
            db_session, 
            chore_id=test_range_chore.id,
            reward_value=reward_value
        )
        
        assert approved_chore is not None
        assert approved_chore.is_approved is True
        assert approved_chore.reward == reward_value
    
    @pytest.mark.asyncio
    async def test_disable_chore(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_chore: Chore
    ):
        """Test disabling a chore."""
        assert test_chore.is_disabled is False
        
        disabled_chore = await chore_repo.disable_chore(
            db_session, 
            chore_id=test_chore.id
        )
        
        assert disabled_chore is not None
        assert disabled_chore.is_disabled is True
    
    @pytest.mark.asyncio
    async def test_get_by_assignee(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test getting all chores for a child in various states."""
        # Create chores in different states
        chores_data = [
            {"is_completed": False, "is_approved": False, "is_disabled": False},
            {"is_completed": True, "is_approved": False, "is_disabled": False},
            {"is_completed": True, "is_approved": True, "is_disabled": False},
            {"is_completed": False, "is_approved": False, "is_disabled": True},
        ]
        
        for i, state in enumerate(chores_data):
            chore = Chore(
                title=f"Chore {i}",
                description="Test",
                reward=5.0,
                assignee_id=test_child_user.id,
                creator_id=test_parent_user.id,
                **state
            )
            db_session.add(chore)
        await db_session.commit()
        
        # Get all child chores
        all_chores = await chore_repo.get_by_assignee(
            db_session, 
            assignee_id=test_child_user.id
        )
        
        # Note: get_by_assignee filters out disabled chores
        assert len(all_chores) == 3  # Only non-disabled chores
        assert all(chore.assignee_id == test_child_user.id for chore in all_chores)
        assert all(not chore.is_disabled for chore in all_chores)
    
    @pytest.mark.asyncio
    async def test_get_completed_by_child(
        self, 
        db_session: AsyncSession, 
        chore_repo: ChoreRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test getting completed and approved chores for a child."""
        # Create chores in different states
        chores_data = [
            {"is_completed": False, "is_approved": False},  # Not completed
            {"is_completed": True, "is_approved": False},   # Completed but not approved
            {"is_completed": True, "is_approved": True},    # Completed and approved
            {"is_completed": True, "is_approved": True},    # Another completed and approved
        ]
        
        for i, state in enumerate(chores_data):
            chore = Chore(
                title=f"Chore {i}",
                description="Test",
                reward=5.0 * (i + 1),
                assignee_id=test_child_user.id,
                creator_id=test_parent_user.id,
                is_disabled=False,
                **state
            )
            db_session.add(chore)
        await db_session.commit()
        
        # Get completed chores
        completed_chores = await chore_repo.get_completed_by_child(
            db_session, 
            child_id=test_child_user.id
        )
        
        # Note: get_completed_by_child returns ALL completed chores, not just approved ones
        assert len(completed_chores) == 3  # 2 approved + 1 not approved
        assert all(chore.is_completed for chore in completed_chores)
        # Filter to only approved ones for reward calculation
        approved_chores = [c for c in completed_chores if c.is_approved]
        assert len(approved_chores) == 2
        assert sum(chore.reward for chore in approved_chores) == 15.0 + 20.0