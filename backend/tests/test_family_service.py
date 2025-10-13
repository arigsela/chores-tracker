"""
Comprehensive tests for family service business logic.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.family import FamilyService
from backend.app.repositories.user import UserRepository
from backend.app.repositories.family import FamilyRepository
from backend.app.core.exceptions import ValidationError, NotFoundError, AuthorizationError
from backend.app.core.security.password import get_password_hash


@pytest.mark.asyncio
class TestFamilyService:
    """Test family service operations."""
    
    async def test_create_family_for_user_success(self, db_session: AsyncSession):
        """Test successful family creation by parent."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create a parent user
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        # Create family
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id, family_name="Test Family"
        )
        
        assert family.name == "Test Family"
        assert len(family.invite_code) == 8
        assert family.invite_code.isupper()
        
        # Verify user is now in the family
        updated_parent = await user_repo.get(db_session, id=parent.id)
        assert updated_parent.family_id == family.id
    
    async def test_create_family_auto_name(self, db_session: AsyncSession):
        """Test family creation with auto-generated name."""
        user_repo = UserRepository()
        family_service = FamilyService()

        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "mom",
                "password": "testpass123",
                "email": "mom@example.com",
                "is_parent": True
            }
        )

        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id
        )

        assert family.name == "mom's Family"

    async def test_create_family_syncs_existing_children_family_id(self, db_session: AsyncSession):
        """
        Test that creating a family automatically syncs existing children's family_id.

        Bug fix test: Previously, when a parent created a family, their children's
        family_id would remain NULL, breaking family-based queries.

        This test ensures:
        1. Children are created before family (parent_id set, family_id NULL)
        2. Parent creates family
        3. All children's family_id are automatically updated to match parent's family
        """
        user_repo = UserRepository()
        family_service = FamilyService()
        family_repo = FamilyRepository()

        # Step 1: Create parent without family
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent_with_kids",
                "password": "testpass123",
                "email": "parent@example.com",
                "is_parent": True
            }
        )

        # Step 2: Create multiple children BEFORE family is created
        child1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "child1",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )

        child2 = await user_repo.create(
            db_session,
            obj_in={
                "username": "child2",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )

        child3 = await user_repo.create(
            db_session,
            obj_in={
                "username": "child3",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )

        # Verify children exist but have no family_id yet
        assert child1.family_id is None
        assert child2.family_id is None
        assert child3.family_id is None
        assert child1.parent_id == parent.id
        assert child2.parent_id == parent.id
        assert child3.parent_id == parent.id

        # Step 3: Parent creates family (THIS IS WHERE THE BUG WAS)
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id, family_name="Test Family"
        )

        # Step 4: Verify parent is in family
        updated_parent = await user_repo.get(db_session, id=parent.id)
        assert updated_parent.family_id == family.id

        # Step 5: THE BUG FIX - Verify ALL children's family_id were automatically synced
        updated_child1 = await user_repo.get(db_session, id=child1.id)
        updated_child2 = await user_repo.get(db_session, id=child2.id)
        updated_child3 = await user_repo.get(db_session, id=child3.id)

        assert updated_child1.family_id == family.id, "Child1's family_id should match parent's family"
        assert updated_child2.family_id == family.id, "Child2's family_id should match parent's family"
        assert updated_child3.family_id == family.id, "Child3's family_id should match parent's family"

        # Step 6: Verify family-based queries now work correctly
        family_children = await family_repo.get_family_children(db_session, family_id=family.id)
        assert len(family_children) == 3, "Family should have 3 children"

        child_usernames = {child.username for child in family_children}
        assert child_usernames == {"child1", "child2", "child3"}

        # Step 7: Verify family members query includes everyone
        family_members = await family_repo.get_family_members(db_session, family_id=family.id)
        assert len(family_members) == 4, "Family should have 4 members (1 parent + 3 children)"

        member_usernames = {member.username for member in family_members}
        assert member_usernames == {"parent_with_kids", "child1", "child2", "child3"}
    
    async def test_create_family_not_parent_fails(self, db_session: AsyncSession):
        """Test that children cannot create families."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create parent first
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        # Create child
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "child1",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )
        
        with pytest.raises(AuthorizationError, match="Only parents can create families"):
            await family_service.create_family_for_user(
                db_session, user_id=child.id
            )
    
    async def test_create_family_user_not_found(self, db_session: AsyncSession):
        """Test family creation with non-existent user."""
        family_service = FamilyService()
        
        with pytest.raises(NotFoundError, match="User with ID 999 not found"):
            await family_service.create_family_for_user(
                db_session, user_id=999
            )
    
    async def test_create_family_user_already_in_family(self, db_session: AsyncSession):
        """Test that user already in family cannot create another."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        # Create first family
        await family_service.create_family_for_user(
            db_session, user_id=parent.id, family_name="First Family"
        )
        
        # Try to create second family
        with pytest.raises(ValidationError, match="User is already a member of a family"):
            await family_service.create_family_for_user(
                db_session, user_id=parent.id, family_name="Second Family"
            )
    
    async def test_join_family_by_code_success(self, db_session: AsyncSession):
        """Test successful family joining via invite code."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create first parent and family
        parent1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent1.id, family_name="Test Family"
        )
        
        # Create second parent
        parent2 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent2",
                "password": "testpass123",
                "email": "parent2@example.com",
                "is_parent": True
            }
        )
        
        # Join family using invite code
        joined_family = await family_service.join_family_by_code(
            db_session, user_id=parent2.id, invite_code=family.invite_code
        )
        
        assert joined_family.id == family.id
        
        # Verify parent2 is now in the family
        updated_parent2 = await user_repo.get(db_session, id=parent2.id)
        assert updated_parent2.family_id == family.id
    
    async def test_join_family_invalid_code(self, db_session: AsyncSession):
        """Test joining family with invalid invite code."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        with pytest.raises(NotFoundError, match="Invalid or expired invite code"):
            await family_service.join_family_by_code(
                db_session, user_id=parent.id, invite_code="INVALID1"
            )
    
    async def test_join_family_child_cannot_join(self, db_session: AsyncSession):
        """Test that children cannot join families directly."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create parent and family
        parent1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent1.id
        )
        
        # Create another parent and child
        parent2 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent2",
                "password": "testpass123",
                "email": "parent2@example.com",
                "is_parent": True
            }
        )
        
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "child1",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent2.id
            }
        )
        
        with pytest.raises(AuthorizationError, match="Only parents can join families"):
            await family_service.join_family_by_code(
                db_session, user_id=child.id, invite_code=family.invite_code
            )
    
    async def test_get_family_members_with_authorization(self, db_session: AsyncSession):
        """Test getting family members with proper authorization."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create family with multiple members
        parent1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent1.id
        )
        
        parent2 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent2",
                "password": "testpass123",
                "email": "parent2@example.com",
                "is_parent": True
            }
        )
        
        await family_service.join_family_by_code(
            db_session, user_id=parent2.id, invite_code=family.invite_code
        )
        
        # Create child for parent1
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "child1",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent1.id
            }
        )
        
        # Update child's family_id after creation
        child = await user_repo.update(
            db_session, id=child.id, obj_in={"family_id": family.id}
        )
        
        # Parent1 should be able to get family members
        members = await family_service.get_family_members(
            db_session, family_id=family.id, requesting_user_id=parent1.id
        )
        
        assert len(members) == 3  # parent1, parent2, child
        member_usernames = {m.username for m in members}
        assert member_usernames == {"parent1", "parent2", "child1"}
    
    async def test_get_family_members_unauthorized(self, db_session: AsyncSession):
        """Test that unauthorized users cannot get family members."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create family
        parent1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent1.id
        )
        
        # Create another parent NOT in the family
        outsider = await user_repo.create(
            db_session,
            obj_in={
                "username": "outsider",
                "password": "testpass123",
                "email": "outsider@example.com",
                "is_parent": True
            }
        )
        
        with pytest.raises(AuthorizationError, match="User does not have access to this family"):
            await family_service.get_family_members(
                db_session, family_id=family.id, requesting_user_id=outsider.id
            )
    
    async def test_generate_new_invite_code_success(self, db_session: AsyncSession):
        """Test generating new invite codes."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id
        )
        
        original_code = family.invite_code
        
        # Generate new code
        new_code = await family_service.generate_new_invite_code(
            db_session, family_id=family.id, requesting_user_id=parent.id
        )
        
        assert new_code != original_code
        assert len(new_code) == 8
        assert new_code.isupper()
    
    async def test_generate_invite_code_non_parent_fails(self, db_session: AsyncSession):
        """Test that children cannot generate invite codes."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id
        )
        
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "child1",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )
        
        # Update child's family_id after creation
        child = await user_repo.update(
            db_session, id=child.id, obj_in={"family_id": family.id}
        )
        
        with pytest.raises(AuthorizationError, match="Only parents can generate invite codes"):
            await family_service.generate_new_invite_code(
                db_session, family_id=family.id, requesting_user_id=child.id
            )
    
    async def test_remove_user_from_family_success(self, db_session: AsyncSession):
        """Test successful user removal from family."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create family with multiple parents
        parent1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent1.id
        )
        
        parent2 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent2",
                "password": "testpass123",
                "email": "parent2@example.com",
                "is_parent": True
            }
        )
        
        await family_service.join_family_by_code(
            db_session, user_id=parent2.id, invite_code=family.invite_code
        )
        
        # Remove parent2 from family
        await family_service.remove_user_from_family(
            db_session, 
            user_id=parent2.id,
            family_id=family.id,
            requesting_user_id=parent1.id
        )
        
        # Verify parent2 is no longer in family
        updated_parent2 = await user_repo.get(db_session, id=parent2.id)
        assert updated_parent2.family_id is None
    
    async def test_remove_last_parent_fails(self, db_session: AsyncSession):
        """Test that last parent cannot be removed from family."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id
        )
        
        with pytest.raises(ValidationError, match="Cannot remove the last parent from a family"):
            await family_service.remove_user_from_family(
                db_session,
                user_id=parent.id,
                family_id=family.id,
                requesting_user_id=parent.id
            )
    
    async def test_validate_family_member_access(self, db_session: AsyncSession):
        """Test family member access validation."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        # Create family with parent and child
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id
        )
        
        child = await user_repo.create(
            db_session,
            obj_in={
                "username": "child1",
                "password": "testpass123",
                "is_parent": False,
                "parent_id": parent.id
            }
        )
        
        # Update child's family_id after creation
        child = await user_repo.update(
            db_session, id=child.id, obj_in={"family_id": family.id}
        )
        
        # Create outsider
        outsider = await user_repo.create(
            db_session,
            obj_in={
                "username": "outsider",
                "password": "testpass123",
                "email": "outsider@example.com",
                "is_parent": True
            }
        )
        
        # Test access validations
        # Same user can access their own data
        assert await family_service.validate_family_member_access(
            db_session, user_id=parent.id, target_user_id=parent.id
        ) is True
        
        # Parent can access child's data
        assert await family_service.validate_family_member_access(
            db_session, user_id=parent.id, target_user_id=child.id
        ) is True
        
        # Child cannot access parent's data
        assert await family_service.validate_family_member_access(
            db_session, user_id=child.id, target_user_id=parent.id
        ) is False
        
        # Outsider cannot access family member data
        assert await family_service.validate_family_member_access(
            db_session, user_id=outsider.id, target_user_id=parent.id
        ) is False
    
    async def test_get_family_stats(self, db_session: AsyncSession):
        """Test getting family statistics."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        family = await family_service.create_family_for_user(
            db_session, user_id=parent.id, family_name="Test Family"
        )
        
        stats = await family_service.get_family_stats(
            db_session, family_id=family.id, requesting_user_id=parent.id
        )
        
        assert stats["name"] == "Test Family"
        assert stats["invite_code"] == family.invite_code
        assert stats["total_members"] == 1
        assert stats["total_parents"] == 1
        assert stats["total_children"] == 0


@pytest.mark.asyncio 
class TestFamilyServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    async def test_invite_code_uniqueness(self, db_session: AsyncSession):
        """Test that invite codes are unique across families."""
        user_repo = UserRepository()
        family_service = FamilyService()
        family_repo = FamilyRepository()
        
        # Create multiple families and ensure unique codes
        invite_codes = set()
        
        for i in range(5):
            parent = await user_repo.create(
                db_session,
                obj_in={
                    "username": f"parent{i}",
                    "password": "testpass123",
                    "email": f"parent{i}@example.com",
                    "is_parent": True
                }
            )
            
            family = await family_service.create_family_for_user(
                db_session, user_id=parent.id
            )
            
            assert family.invite_code not in invite_codes
            invite_codes.add(family.invite_code)
        
        assert len(invite_codes) == 5
    
    async def test_concurrent_family_creation(self, db_session: AsyncSession):
        """Test handling of concurrent family operations."""
        user_repo = UserRepository()
        family_service = FamilyService()
        
        parent1 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent1",
                "password": "testpass123",
                "email": "parent1@example.com",
                "is_parent": True
            }
        )
        
        parent2 = await user_repo.create(
            db_session,
            obj_in={
                "username": "parent2",
                "password": "testpass123",
                "email": "parent2@example.com",
                "is_parent": True
            }
        )
        
        # Create family for parent1
        family1 = await family_service.create_family_for_user(
            db_session, user_id=parent1.id
        )
        
        # Parent2 should be able to join the family
        joined_family = await family_service.join_family_by_code(
            db_session, user_id=parent2.id, invite_code=family1.invite_code
        )
        
        assert joined_family.id == family1.id
        
        # Both parents should now be in the same family
        updated_parent1 = await user_repo.get(db_session, id=parent1.id)
        updated_parent2 = await user_repo.get(db_session, id=parent2.id)
        
        assert updated_parent1.family_id == updated_parent2.family_id
    
    async def test_family_operations_with_nonexistent_ids(self, db_session: AsyncSession):
        """Test family operations with non-existent IDs."""
        family_service = FamilyService()
        
        # Test with non-existent family ID
        with pytest.raises(AuthorizationError):
            await family_service.get_family_members(
                db_session, family_id=999, requesting_user_id=1
            )
        
        # Test with non-existent user ID (returns None instead of raising exception)
        result = await family_service.get_user_family_context(
            db_session, user_id=999
        )
        assert result is None