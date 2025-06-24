"""
Test service layer business logic.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.services.user_service import UserService
from backend.app.services.chore_service import ChoreService
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash


class TestUserServiceBusinessLogic:
    """Test UserService business logic methods."""
    
    @pytest.mark.asyncio
    async def test_register_parent_without_email(self, db_session: AsyncSession):
        """Test that parent registration requires email."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="parent_no_email",
                password="password123",
                is_parent=True
                # Missing email!
            )
        
        assert exc_info.value.status_code == 422
        assert "Email is required for parent accounts" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_parent_invalid_email(self, db_session: AsyncSession):
        """Test that parent registration validates email format."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="parent_bad_email",
                password="password123",
                is_parent=True,
                email="not-an-email"
            )
        
        assert exc_info.value.status_code == 422
        assert "Invalid email format" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_child_without_parent(self, db_session: AsyncSession):
        """Test that child registration requires parent_id."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="orphan_child",
                password="password123",
                is_parent=False
                # Missing parent_id!
            )
        
        assert exc_info.value.status_code == 422
        assert "Parent ID is required for child accounts" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_child_with_nonexistent_parent(self, db_session: AsyncSession):
        """Test that child registration validates parent exists."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="child_fake_parent",
                password="password123",
                is_parent=False,
                parent_id=99999  # Non-existent
            )
        
        assert exc_info.value.status_code == 404
        assert "Parent user not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, db_session: AsyncSession):
        """Test that duplicate usernames are rejected."""
        user_service = UserService()
        
        # Create first user
        await user_service.register_user(
            db_session,
            username="duplicate_test",
            password="password123",
            email="first@test.com",
            is_parent=True
        )
        
        # Try to create with same username
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="duplicate_test",
                password="password123",
                email="second@test.com",
                is_parent=True
            )
        
        assert exc_info.value.status_code == 400
        assert "Username already taken" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db_session: AsyncSession):
        """Test that duplicate emails are rejected."""
        user_service = UserService()
        
        # Create first user
        await user_service.register_user(
            db_session,
            username="user1_dup_email",
            password="password123",
            email="duplicate@test.com",
            is_parent=True
        )
        
        # Try to create with same email
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="user2_dup_email",
                password="password123",
                email="duplicate@test.com",
                is_parent=True
            )
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_register_password_too_short(self, db_session: AsyncSession):
        """Test password length validation."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register_user(
                db_session,
                username="short_pass",
                password="short",  # Too short!
                email="short@test.com",
                is_parent=True
            )
        
        assert exc_info.value.status_code == 422
        assert "Password must be at least 8 characters long" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_wrong_username(self, db_session: AsyncSession):
        """Test authentication with wrong username."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.authenticate(
                db_session,
                username="nonexistent",
                password="password123"
            )
        
        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, db_session: AsyncSession):
        """Test authentication with wrong password."""
        user_service = UserService()
        
        # Create user
        await user_service.register_user(
            db_session,
            username="test_auth_user",
            password="correct_password",
            email="auth@test.com",
            is_parent=True
        )
        
        # Try wrong password
        with pytest.raises(HTTPException) as exc_info:
            await user_service.authenticate(
                db_session,
                username="test_auth_user",
                password="wrong_password"
            )
        
        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, db_session: AsyncSession):
        """Test authentication with inactive user."""
        user_service = UserService()
        
        # Create user
        user = User(
            username="inactive_user",
            email="inactive@test.com",
            hashed_password=get_password_hash("password123"),
            is_parent=True,
            is_active=False  # Inactive!
        )
        db_session.add(user)
        await db_session.commit()
        
        # Try to authenticate
        with pytest.raises(HTTPException) as exc_info:
            await user_service.authenticate(
                db_session,
                username="inactive_user",
                password="password123"
            )
        
        assert exc_info.value.status_code == 401
        assert "User is inactive" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token_or_id(self, db_session: AsyncSession):
        """Test get_current_user without token or user_id."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_current_user(db_session)
        
        assert exc_info.value.status_code == 401
        assert "No user identification provided" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent(self, db_session: AsyncSession):
        """Test get_current_user with non-existent user_id."""
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_current_user(db_session, user_id=99999)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_current_user_inactive(self, db_session: AsyncSession):
        """Test get_current_user with inactive user."""
        # Create inactive user
        user = User(
            username="inactive_current",
            email="inactive_current@test.com",
            hashed_password=get_password_hash("password123"),
            is_parent=True,
            is_active=False
        )
        db_session.add(user)
        await db_session.commit()
        
        user_service = UserService()
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_current_user(db_session, user_id=user.id)
        
        assert exc_info.value.status_code == 401
        assert "Inactive user" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_reset_child_password_not_parent(self, db_session: AsyncSession):
        """Test resetting password for non-child account."""
        user_service = UserService()
        
        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_reset",
            password="password123",
            email="parent1@test.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_reset",
            password="password123",
            email="parent2@test.com",
            is_parent=True
        )
        
        # Try to reset password for another parent
        with pytest.raises(HTTPException) as exc_info:
            await user_service.reset_child_password(
                db_session,
                parent_id=parent1.id,
                child_id=parent2.id,
                new_password="newpass123"
            )
        
        assert exc_info.value.status_code == 403
        assert "Cannot reset password for a parent account" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_reset_child_password_wrong_parent(self, db_session: AsyncSession):
        """Test resetting password for child of different parent."""
        user_service = UserService()
        
        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_wrong",
            password="password123",
            email="parent1w@test.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_wrong",
            password="password123",
            email="parent2w@test.com",
            is_parent=True
        )
        
        # Create child for parent2
        child = await user_service.register_user(
            db_session,
            username="child_wrong_parent",
            password="password123",
            is_parent=False,
            parent_id=parent2.id
        )
        
        # Parent1 tries to reset child's password
        with pytest.raises(HTTPException) as exc_info:
            await user_service.reset_child_password(
                db_session,
                parent_id=parent1.id,
                child_id=child.id,
                new_password="newpass123"
            )
        
        assert exc_info.value.status_code == 403
        assert "You can only reset passwords for your own children" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_reset_child_password_too_short(self, db_session: AsyncSession):
        """Test resetting password with too short password."""
        user_service = UserService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_short_pass",
            password="password123",
            email="parentsp@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_short_pass",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Try to set too short password
        with pytest.raises(HTTPException) as exc_info:
            await user_service.reset_child_password(
                db_session,
                parent_id=parent.id,
                child_id=child.id,
                new_password="123"  # Too short!
            )
        
        assert exc_info.value.status_code == 422
        assert "Password must be at least 4 characters long" in str(exc_info.value.detail)


class TestChoreServiceBusinessLogic:
    """Test ChoreService business logic methods."""
    
    @pytest.mark.asyncio
    async def test_create_chore_assignee_not_found(self, db_session: AsyncSession):
        """Test creating chore with non-existent assignee."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent
        parent = await user_service.register_user(
            db_session,
            username="parent_chore_test",
            password="password123",
            email="parentchore@test.com",
            is_parent=True
        )
        
        # Try to create chore with non-existent assignee
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.create_chore(
                db_session,
                creator_id=parent.id,
                chore_data={
                    "title": "Test Chore",
                    "description": "Test",
                    "reward": 5.0,
                    "assignee_id": 99999  # Non-existent
                }
            )
        
        assert exc_info.value.status_code == 404
        assert "Assignee not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_chore_assignee_wrong_parent(self, db_session: AsyncSession):
        """Test creating chore for child of different parent."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_chore",
            password="password123",
            email="parent1c@test.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_chore",
            password="password123",
            email="parent2c@test.com",
            is_parent=True
        )
        
        # Create child for parent2
        child = await user_service.register_user(
            db_session,
            username="child_other_parent",
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
                    "title": "Test Chore",
                    "description": "Test",
                    "reward": 5.0,
                    "assignee_id": child.id
                }
            )
        
        assert exc_info.value.status_code == 403
        assert "You can only assign chores to your own children" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_complete_chore_not_assignee(self, db_session: AsyncSession):
        """Test completing chore by non-assignee."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and two children
        parent = await user_service.register_user(
            db_session,
            username="parent_complete",
            password="password123",
            email="parentcomp@test.com",
            is_parent=True
        )
        
        child1 = await user_service.register_user(
            db_session,
            username="child1_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        child2 = await user_service.register_user(
            db_session,
            username="child2_complete",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create chore for child1
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Child1 Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": child1.id
            }
        )
        
        # Child2 tries to complete it
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child2.id
            )
        
        assert exc_info.value.status_code == 403
        assert "You are not the assignee of this chore" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_complete_disabled_chore(self, db_session: AsyncSession):
        """Test completing a disabled chore."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_disabled",
            password="password123",
            email="parentdis@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_disabled",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create and disable chore
        chore = Chore(
            title="Disabled Chore",
            description="Test",
            reward=5.0,
            is_range_reward=False,
            cooldown_days=0,
            is_recurring=False,
            creator_id=parent.id,
            assignee_id=child.id,
            is_completed=False,
            is_approved=False,
            is_disabled=True  # Disabled!
        )
        db_session.add(chore)
        await db_session.commit()
        
        # Try to complete it
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.complete_chore(
                db_session,
                chore_id=chore.id,
                user_id=child.id
            )
        
        assert exc_info.value.status_code == 400
        assert "Cannot complete a disabled chore" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_approve_chore_not_creator(self, db_session: AsyncSession):
        """Test approving chore by non-creator."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_approve",
            password="password123",
            email="parent1a@test.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_approve",
            password="password123",
            email="parent2a@test.com",
            is_parent=True
        )
        
        # Create child for parent1
        child = await user_service.register_user(
            db_session,
            username="child_approve",
            password="password123",
            is_parent=False,
            parent_id=parent1.id
        )
        
        # Parent1 creates chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent1.id,
            chore_data={
                "title": "Test Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": child.id
            }
        )
        
        # Complete the chore
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        
        # Parent2 tries to approve
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent2.id
            )
        
        assert exc_info.value.status_code == 403
        assert "You can only approve chores you created" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_approve_uncompleted_chore(self, db_session: AsyncSession):
        """Test approving chore that isn't completed."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_uncomp",
            password="password123",
            email="parentunc@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_uncomp",
            password="password123",
            is_parent=False,
            parent_id=parent.id
        )
        
        # Create chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent.id,
            chore_data={
                "title": "Uncompleted Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": child.id
            }
        )
        
        # Try to approve without completing
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.approve_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent.id
            )
        
        assert exc_info.value.status_code == 400
        assert "Chore must be completed before approval" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_completed_chore(self, db_session: AsyncSession):
        """Test updating a completed chore."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create parent and child
        parent = await user_service.register_user(
            db_session,
            username="parent_upd_comp",
            password="password123",
            email="parentupdc@test.com",
            is_parent=True
        )
        
        child = await user_service.register_user(
            db_session,
            username="child_upd_comp",
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
                "assignee_id": child.id
            }
        )
        
        await chore_service.complete_chore(
            db_session,
            chore_id=chore.id,
            user_id=child.id
        )
        
        # Try to update
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.update_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent.id,
                update_data={"title": "Updated Title"}
            )
        
        assert exc_info.value.status_code == 400
        assert "Cannot update completed or approved chores" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_disable_chore_not_creator(self, db_session: AsyncSession):
        """Test disabling chore by non-creator."""
        user_service = UserService()
        chore_service = ChoreService()
        
        # Create two parents
        parent1 = await user_service.register_user(
            db_session,
            username="parent1_disable",
            password="password123",
            email="parent1d@test.com",
            is_parent=True
        )
        
        parent2 = await user_service.register_user(
            db_session,
            username="parent2_disable",
            password="password123",
            email="parent2d@test.com",
            is_parent=True
        )
        
        # Create child for parent1
        child = await user_service.register_user(
            db_session,
            username="child_disable",
            password="password123",
            is_parent=False,
            parent_id=parent1.id
        )
        
        # Parent1 creates chore
        chore = await chore_service.create_chore(
            db_session,
            creator_id=parent1.id,
            chore_data={
                "title": "Test Chore",
                "description": "Test",
                "reward": 5.0,
                "assignee_id": child.id
            }
        )
        
        # Parent2 tries to disable
        with pytest.raises(HTTPException) as exc_info:
            await chore_service.disable_chore(
                db_session,
                chore_id=chore.id,
                parent_id=parent2.id
            )
        
        assert exc_info.value.status_code == 403
        assert "You can only disable chores you created" in str(exc_info.value.detail)