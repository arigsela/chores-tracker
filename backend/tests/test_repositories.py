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
        """Test getting available chores for a child using ChoreAssignmentRepository."""
        from backend.app.models.chore_assignment import ChoreAssignment
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository

        assignment_repo = ChoreAssignmentRepository()

        # Create multiple chores with different states
        chores_data = [
            {
                "title": "Available Chore 1",
                "description": "Test",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            },
            {
                "title": "Completed Chore",
                "description": "Test",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            },
            {
                "title": "Disabled Chore",
                "description": "Test",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": True
            },
            {
                "title": "Available Chore 2",
                "description": "Test",
                "reward": 10.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            }
        ]

        for i, chore_data in enumerate(chores_data):
            chore = Chore(**chore_data)
            db_session.add(chore)
            await db_session.flush()

            # Create assignment for each chore
            assignment = ChoreAssignment(
                chore_id=chore.id,
                assignee_id=test_child_user.id,
                is_completed=(i == 1),  # Second chore is completed
                is_approved=False
            )
            db_session.add(assignment)

        await db_session.commit()

        # Get available assignments using new repository
        available_assignments = await assignment_repo.get_available_for_child(
            db_session,
            assignee_id=test_child_user.id
        )

        assert len(available_assignments) == 2
        assert all(not assignment.is_completed for assignment in available_assignments)
        assert all(not assignment.chore.is_disabled for assignment in available_assignments)
        assert all(assignment.assignee_id == test_child_user.id for assignment in available_assignments)
    
    @pytest.mark.asyncio
    async def test_get_pending_approval(
        self,
        db_session: AsyncSession,
        chore_repo: ChoreRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test getting assignments pending approval."""
        from backend.app.models.chore_assignment import ChoreAssignment
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository

        assignment_repo = ChoreAssignmentRepository()

        # Create chores with different assignment states
        chores_data = [
            {
                "title": "Pending Approval 1",
                "description": "Test",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            },
            {
                "title": "Already Approved",
                "description": "Test",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            },
            {
                "title": "Not Completed",
                "description": "Test",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            },
            {
                "title": "Pending Approval 2",
                "description": "Test",
                "reward": 10.0,
                "is_range_reward": False,
                "cooldown_days": 0,
                "is_recurring": False,
                "assignment_mode": "single",
                "creator_id": test_parent_user.id,
                "is_disabled": False
            }
        ]

        assignment_states = [
            {"is_completed": True, "is_approved": False},   # Pending approval
            {"is_completed": True, "is_approved": True},    # Already approved
            {"is_completed": False, "is_approved": False},  # Not completed
            {"is_completed": True, "is_approved": False}    # Pending approval
        ]

        for chore_data, assignment_state in zip(chores_data, assignment_states):
            chore = Chore(**chore_data)
            db_session.add(chore)
            await db_session.flush()

            # Create assignment with specific state
            assignment = ChoreAssignment(
                chore_id=chore.id,
                assignee_id=test_child_user.id,
                **assignment_state
            )
            db_session.add(assignment)

        await db_session.commit()

        # Get pending approval assignments
        pending_assignments = await assignment_repo.get_pending_approval(
            db_session,
            creator_id=test_parent_user.id
        )

        assert len(pending_assignments) == 2
        assert all(assignment.is_completed for assignment in pending_assignments)
        assert all(not assignment.is_approved for assignment in pending_assignments)
        assert all(assignment.chore.creator_id == test_parent_user.id for assignment in pending_assignments)
    
    @pytest.mark.asyncio
    async def test_mark_completed(
        self,
        db_session: AsyncSession,
        chore_repo: ChoreRepository,
        test_chore: Chore,
        test_child_user: User
    ):
        """Test completing a chore assignment."""
        from backend.app.models.chore_assignment import ChoreAssignment
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository

        assignment_repo = ChoreAssignmentRepository()

        # Get the assignment created by the test_chore fixture
        assignment = await assignment_repo.get_by_chore_and_assignee(
            db_session,
            chore_id=test_chore.id,
            assignee_id=test_child_user.id
        )

        assert assignment is not None
        assert assignment.is_completed is False

        # Mark the assignment as completed
        completed_assignment = await assignment_repo.mark_completed(
            db_session,
            assignment_id=assignment.id
        )

        assert completed_assignment is not None
        assert completed_assignment.is_completed is True
        assert completed_assignment.completion_date is not None
    
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
        test_chore: Chore,
        test_child_user: User
    ):
        """Test approving an assignment with fixed reward."""
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository

        assignment_repo = ChoreAssignmentRepository()

        # Get the assignment
        assignment = await assignment_repo.get_by_chore_and_assignee(
            db_session,
            chore_id=test_chore.id,
            assignee_id=test_child_user.id
        )

        # First complete the assignment
        await assignment_repo.mark_completed(db_session, assignment_id=assignment.id)

        # Then approve it
        approved_assignment = await assignment_repo.approve_assignment(
            db_session,
            assignment_id=assignment.id,
            reward_value=None  # Fixed reward doesn't need value
        )

        assert approved_assignment is not None
        assert approved_assignment.is_approved is True
        assert approved_assignment.chore.reward == test_chore.reward
    
    @pytest.mark.asyncio
    async def test_approve_chore_range_reward(
        self,
        db_session: AsyncSession,
        chore_repo: ChoreRepository,
        test_range_chore: Chore,
        test_child_user: User
    ):
        """Test approving an assignment with range reward."""
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository

        assignment_repo = ChoreAssignmentRepository()

        # Get the assignment
        assignment = await assignment_repo.get_by_chore_and_assignee(
            db_session,
            chore_id=test_range_chore.id,
            assignee_id=test_child_user.id
        )

        # First complete the assignment
        await assignment_repo.mark_completed(db_session, assignment_id=assignment.id)

        # Then approve it with specific reward
        reward_value = 3.0  # Between min (2.0) and max (4.0)
        approved_assignment = await assignment_repo.approve_assignment(
            db_session,
            assignment_id=assignment.id,
            reward_value=reward_value
        )

        assert approved_assignment is not None
        assert approved_assignment.is_approved is True
        assert approved_assignment.approval_reward == reward_value
    
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
        """Test getting all assignments for a child in various states."""
        from backend.app.models.chore_assignment import ChoreAssignment
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository

        assignment_repo = ChoreAssignmentRepository()

        # Create chores in different states with assignments
        assignment_states = [
            {"is_completed": False, "is_approved": False, "is_disabled": False},
            {"is_completed": True, "is_approved": False, "is_disabled": False},
            {"is_completed": True, "is_approved": True, "is_disabled": False},
            {"is_completed": False, "is_approved": False, "is_disabled": True},
        ]

        for i, state in enumerate(assignment_states):
            chore = Chore(
                title=f"Chore {i}",
                description="Test",
                reward=5.0,
                is_range_reward=False,
                cooldown_days=0,
                is_recurring=False,
                assignment_mode="single",
                creator_id=test_parent_user.id,
                is_disabled=state["is_disabled"]
            )
            db_session.add(chore)
            await db_session.flush()

            # Create assignment with completion/approval state
            assignment = ChoreAssignment(
                chore_id=chore.id,
                assignee_id=test_child_user.id,
                is_completed=state["is_completed"],
                is_approved=state["is_approved"]
            )
            db_session.add(assignment)

        await db_session.commit()

        # Get all assignments for the child
        all_assignments = await assignment_repo.get_by_assignee(
            db_session,
            assignee_id=test_child_user.id
        )

        # Should get all 4 assignments (including disabled chore)
        assert len(all_assignments) == 4
        assert all(assignment.assignee_id == test_child_user.id for assignment in all_assignments)
    
    @pytest.mark.asyncio
    async def test_get_completed_by_child(
        self,
        db_session: AsyncSession,
        chore_repo: ChoreRepository,
        test_parent_user: User,
        test_child_user: User
    ):
        """Test getting assignment history (completed and approved) for a child."""
        from backend.app.models.chore_assignment import ChoreAssignment
        from backend.app.repositories.chore_assignment import ChoreAssignmentRepository
        from datetime import datetime

        assignment_repo = ChoreAssignmentRepository()

        # Create chores with different assignment states
        assignment_states = [
            {"is_completed": False, "is_approved": False},  # Not completed
            {"is_completed": True, "is_approved": False},   # Completed but not approved
            {"is_completed": True, "is_approved": True},    # Completed and approved
            {"is_completed": True, "is_approved": True},    # Another completed and approved
        ]

        for i, state in enumerate(assignment_states):
            chore = Chore(
                title=f"Chore {i}",
                description="Test",
                reward=5.0 * (i + 1),
                is_range_reward=False,
                cooldown_days=0,
                is_recurring=False,
                assignment_mode="single",
                creator_id=test_parent_user.id,
                is_disabled=False
            )
            db_session.add(chore)
            await db_session.flush()

            # Create assignment with state
            assignment = ChoreAssignment(
                chore_id=chore.id,
                assignee_id=test_child_user.id,
                is_completed=state["is_completed"],
                is_approved=state["is_approved"],
                approval_date=datetime.utcnow() if state["is_approved"] else None
            )
            db_session.add(assignment)

        await db_session.commit()

        # Get assignment history (approved assignments)
        approved_assignments = await assignment_repo.get_assignment_history(
            db_session,
            assignee_id=test_child_user.id
        )

        # Should only get approved assignments
        assert len(approved_assignments) == 2
        assert all(assignment.is_approved for assignment in approved_assignments)
        assert all(assignment.is_completed for assignment in approved_assignments)

        # Verify reward calculation
        total_reward = sum(assignment.chore.reward for assignment in approved_assignments)
        assert total_reward == 15.0 + 20.0