from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.family import FamilyRepository
from ..repositories.user import UserRepository
from ..models.family import Family
from ..models.user import User
from ..core.exceptions import ValidationError, NotFoundError, AuthorizationError
from ..core.metrics import record_family_event


class FamilyService:
    """Service layer for family-related business operations."""
    
    def __init__(self):
        self.family_repo = FamilyRepository()
        self.user_repo = UserRepository()
    
    async def create_family_for_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        family_name: Optional[str] = None
    ) -> Family:
        """Create a new family and assign the user as the first member."""
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        if not user.is_parent:
            raise AuthorizationError("Only parents can create families")
        
        if user.family_id:
            raise ValidationError("User is already a member of a family")

        family = await self.family_repo.create_family_for_user(
            db, user_id=user_id, family_name=family_name
        )

        # Record family creation metric
        record_family_event(event_type='created')

        return family
    
    async def join_family_by_code(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        invite_code: str
    ) -> Family:
        """Join an existing family using an invite code."""
        user = await self.user_repo.get(db, id=user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        if not user.is_parent:
            raise AuthorizationError("Only parents can join families")
        
        if user.family_id:
            raise ValidationError("User is already a member of a family")
        
        family = await self.family_repo.get_by_invite_code(db, invite_code=invite_code)
        if not family:
            raise NotFoundError("Invalid or expired invite code")

        # Update user's family_id
        await self.user_repo.update(db, id=user_id, obj_in={"family_id": family.id})

        # Record family join metric
        record_family_event(event_type='joined')

        return family
    
    async def get_user_family_context(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int
    ) -> Optional[Family]:
        """Get the family context for a user."""
        return await self.family_repo.get_user_family_context(db, user_id=user_id)
    
    async def get_family_members(
        self, 
        db: AsyncSession, 
        *, 
        family_id: int, 
        requesting_user_id: int
    ) -> List[User]:
        """Get all members of a family (requires family membership)."""
        # Validate user has access to this family
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("User does not have access to this family")
        
        return await self.family_repo.get_family_members(db, family_id=family_id)
    
    async def get_family_children(
        self, 
        db: AsyncSession, 
        *, 
        family_id: int, 
        requesting_user_id: int
    ) -> List[User]:
        """Get child members of a family (requires family membership)."""
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("User does not have access to this family")
        
        return await self.family_repo.get_family_children(db, family_id=family_id)
    
    async def get_family_parents(
        self, 
        db: AsyncSession, 
        *, 
        family_id: int, 
        requesting_user_id: int
    ) -> List[User]:
        """Get parent members of a family (requires family membership)."""
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("User does not have access to this family")
        
        return await self.family_repo.get_family_parents(db, family_id=family_id)
    
    async def generate_new_invite_code(
        self, 
        db: AsyncSession, 
        *, 
        family_id: int, 
        requesting_user_id: int, 
        expires_in_days: Optional[int] = None
    ) -> str:
        """Generate a new invite code for a family (parent only)."""
        # Validate user has access and is a parent
        requesting_user = await self.user_repo.get(db, id=requesting_user_id)
        if not requesting_user:
            raise NotFoundError(f"User with ID {requesting_user_id} not found")
        
        if not requesting_user.is_parent:
            raise AuthorizationError("Only parents can generate invite codes")
        
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("User does not have access to this family")
        
        return await self.family_repo.generate_new_invite_code(
            db, family_id=family_id, expires_in_days=expires_in_days
        )
    
    async def get_family_stats(
        self, 
        db: AsyncSession, 
        *, 
        family_id: int, 
        requesting_user_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive family statistics (requires family membership)."""
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("User does not have access to this family")
        
        return await self.family_repo.get_family_stats(db, family_id=family_id)
    
    async def remove_user_from_family(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        family_id: int, 
        requesting_user_id: int
    ) -> None:
        """Remove a user from a family (parent only, cannot remove self if only parent)."""
        # Validate requesting user is a parent in the family
        requesting_user = await self.user_repo.get(db, id=requesting_user_id)
        if not requesting_user:
            raise NotFoundError(f"Requesting user with ID {requesting_user_id} not found")
        
        if not requesting_user.is_parent:
            raise AuthorizationError("Only parents can remove users from families")
        
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("Requesting user does not have access to this family")
        
        # Validate user to remove exists and is in the family
        user_to_remove = await self.user_repo.get(db, id=user_id)
        if not user_to_remove:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        if user_to_remove.family_id != family_id:
            raise ValidationError("User is not a member of this family")
        
        # Check if this would leave the family without parents
        if user_to_remove.is_parent:
            family_parents = await self.family_repo.get_family_parents(db, family_id=family_id)
            if len(family_parents) <= 1:
                raise ValidationError("Cannot remove the last parent from a family")
        
        # Remove user from family
        await self.user_repo.update(db, id=user_id, obj_in={"family_id": None})
    
    async def transfer_family_ownership(
        self, 
        db: AsyncSession, 
        *, 
        family_id: int, 
        new_owner_id: int, 
        requesting_user_id: int
    ) -> None:
        """Transfer family ownership to another parent (for future family admin features)."""
        # Validate requesting user is a parent in the family
        requesting_user = await self.user_repo.get(db, id=requesting_user_id)
        if not requesting_user:
            raise NotFoundError(f"Requesting user with ID {requesting_user_id} not found")
        
        if not requesting_user.is_parent:
            raise AuthorizationError("Only parents can transfer family ownership")
        
        if not await self.family_repo.validate_family_access(db, user_id=requesting_user_id, family_id=family_id):
            raise AuthorizationError("Requesting user does not have access to this family")
        
        # Validate new owner exists and is a parent in the family
        new_owner = await self.user_repo.get(db, id=new_owner_id)
        if not new_owner:
            raise NotFoundError(f"New owner with ID {new_owner_id} not found")
        
        if not new_owner.is_parent:
            raise ValidationError("New owner must be a parent")
        
        if new_owner.family_id != family_id:
            raise ValidationError("New owner must be a member of this family")
        
        # Note: Actual ownership transfer logic would be implemented here
        # For now, this is a placeholder for future family admin features
        pass
    
    async def validate_family_member_access(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        target_user_id: int
    ) -> bool:
        """Validate that a user can access another user's data (same family)."""
        user = await self.user_repo.get(db, id=user_id)
        target_user = await self.user_repo.get(db, id=target_user_id)
        
        if not user or not target_user:
            return False
        
        # Same user can always access their own data
        if user_id == target_user_id:
            return True
        
        # Users must be in the same family
        if not user.family_id or user.family_id != target_user.family_id:
            return False
        
        # Parents can access any family member's data
        if user.is_parent:
            return True
        
        # Children can only access their own data (covered above)
        return False
    
    async def cleanup_expired_invite_codes(self, db: AsyncSession) -> int:
        """Clean up expired invite codes (admin/maintenance operation)."""
        return await self.family_repo.cleanup_expired_invite_codes(db)