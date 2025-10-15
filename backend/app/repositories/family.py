from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import secrets
import string

from .base import BaseRepository
from ..models.family import Family
from ..models.user import User


class FamilyRepository(BaseRepository[Family]):
    """Repository for Family model operations."""
    
    def __init__(self):
        super().__init__(Family)
    
    async def get_by_invite_code(self, db: AsyncSession, *, invite_code: str) -> Optional[Family]:
        """Get family by valid (non-expired) invite code."""
        result = await db.execute(
            select(Family).where(
                Family.invite_code == invite_code.upper(),
                # Check if code is not expired (NULL means no expiry)
                (Family.invite_code_expires_at.is_(None)) | 
                (Family.invite_code_expires_at > datetime.utcnow())
            )
        )
        return result.scalars().first()
    
    async def get_family_members(self, db: AsyncSession, *, family_id: int) -> List[User]:
        """Get all members of a family."""
        result = await db.execute(
            select(User)
            .where(User.family_id == family_id)
            .options(
                joinedload(User.chore_assignments),
                joinedload(User.chores_created)
            )
            .order_by(User.is_parent.desc(), User.username)
        )
        return result.unique().scalars().all()
    
    async def get_family_parents(self, db: AsyncSession, *, family_id: int) -> List[User]:
        """Get parent members of a family."""
        result = await db.execute(
            select(User)
            .where(
                User.family_id == family_id,
                User.is_parent == True
            )
            .order_by(User.username)
        )
        return result.scalars().all()
    
    async def get_family_children(self, db: AsyncSession, *, family_id: int) -> List[User]:
        """Get child members of a family."""
        result = await db.execute(
            select(User)
            .where(
                User.family_id == family_id,
                User.is_parent == False
            )
            .options(
                joinedload(User.chore_assignments),
                joinedload(User.parent)
            )
            .order_by(User.username)
        )
        return result.unique().scalars().all()
    
    async def generate_unique_invite_code(self, db: AsyncSession) -> str:
        """Generate a unique 8-character invite code."""
        max_attempts = 10
        characters = string.ascii_uppercase + string.digits
        
        for _ in range(max_attempts):
            # Generate 8-character code
            invite_code = ''.join(secrets.choice(characters) for _ in range(8))
            
            # Check if code already exists
            existing = await db.execute(
                select(Family).where(Family.invite_code == invite_code)
            )
            
            if not existing.scalars().first():
                return invite_code
        
        # If we can't generate a unique code, raise an error
        raise ValueError("Unable to generate unique invite code after 10 attempts")
    
    async def create_family_for_user(self, db: AsyncSession, *, user_id: int, family_name: Optional[str] = None) -> Family:
        """Create a new family and assign the user as the first member."""
        # Get the user to create family name
        user = await db.execute(select(User).where(User.id == user_id))
        user_obj = user.scalars().first()

        if not user_obj:
            raise ValueError(f"User with ID {user_id} not found")

        if not user_obj.is_parent:
            raise ValueError("Only parents can create families")

        # Generate family name if not provided
        if not family_name:
            family_name = f"{user_obj.username}'s Family"

        # Generate unique invite code
        invite_code = await self.generate_unique_invite_code(db)

        # Create family
        family_data = {
            "name": family_name,
            "invite_code": invite_code,
            "invite_code_expires_at": None  # No expiry by default
        }

        family = await super().create(db, obj_in=family_data)

        # Assign user to the family using a separate user repository instance
        from .user import UserRepository
        user_repo = UserRepository()
        await user_repo.update(db, id=user_id, obj_in={"family_id": family.id})

        # FIX: Update all existing children's family_id to match parent's family
        # This ensures children are discoverable via family-based queries
        children_result = await db.execute(
            select(User).where(User.parent_id == user_id)
        )
        children = children_result.scalars().all()

        for child in children:
            await user_repo.update(db, id=child.id, obj_in={"family_id": family.id})

        return family
    
    async def generate_new_invite_code(self, db: AsyncSession, *, family_id: int, expires_in_days: Optional[int] = None) -> str:
        """Generate new invite code for a family and invalidate the old one."""
        # Generate new unique code
        new_invite_code = await self.generate_unique_invite_code(db)
        
        # Set expiration if specified
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Update family with new invite code
        await self.update(db, id=family_id, obj_in={
            "invite_code": new_invite_code,
            "invite_code_expires_at": expires_at
        })
        
        return new_invite_code
    
    async def get_family_stats(self, db: AsyncSession, *, family_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a family with multi-assignment support."""
        result = await db.execute(text("""
            SELECT
                f.name,
                f.invite_code,
                f.created_at,
                COUNT(DISTINCT u.id) as total_members,
                COUNT(DISTINCT CASE WHEN u.is_parent = 1 THEN u.id END) as total_parents,
                COUNT(DISTINCT CASE WHEN u.is_parent = 0 THEN u.id END) as total_children,
                COUNT(DISTINCT c.id) as total_chores,
                COUNT(DISTINCT CASE WHEN ca.is_completed = 1 THEN ca.id END) as completed_chores,
                COUNT(DISTINCT CASE WHEN ca.is_completed = 1 AND ca.is_approved = 1 THEN ca.id END) as approved_chores,
                COALESCE(SUM(CASE WHEN ca.is_completed = 1 AND ca.is_approved = 1 THEN
                    COALESCE(ca.approval_reward, c.reward, 0) END), 0) as total_rewards_earned
            FROM families f
            LEFT JOIN users u ON u.family_id = f.id
            LEFT JOIN chores c ON c.creator_id = u.id
            LEFT JOIN chore_assignments ca ON (ca.chore_id = c.id OR ca.assignee_id = u.id)
            WHERE f.id = :family_id
            GROUP BY f.id, f.name, f.invite_code, f.created_at
        """), {"family_id": family_id})
        
        row = result.fetchone()
        if not row:
            return {}
        
        return {
            "family_id": family_id,
            "name": row[0],
            "invite_code": row[1],
            "created_at": row[2],
            "total_members": row[3] or 0,
            "total_parents": row[4] or 0,
            "total_children": row[5] or 0,
            "total_chores": row[6] or 0,
            "completed_chores": row[7] or 0,
            "approved_chores": row[8] or 0,
            "total_rewards_earned": float(row[9] or 0)
        }
    
    async def get_families_with_member_counts(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get families with member counts for admin/debugging purposes."""
        result = await db.execute(text("""
            SELECT 
                f.id,
                f.name,
                f.invite_code,
                f.created_at,
                COUNT(u.id) as member_count,
                SUM(CASE WHEN u.is_parent = 1 THEN 1 ELSE 0 END) as parent_count,
                SUM(CASE WHEN u.is_parent = 0 THEN 1 ELSE 0 END) as child_count
            FROM families f
            LEFT JOIN users u ON u.family_id = f.id
            GROUP BY f.id, f.name, f.invite_code, f.created_at
            ORDER BY f.created_at DESC
            LIMIT :limit OFFSET :skip
        """), {"limit": limit, "skip": skip})
        
        families = []
        for row in result:
            families.append({
                "id": row[0],
                "name": row[1],
                "invite_code": row[2],
                "created_at": row[3],
                "member_count": row[4] or 0,
                "parent_count": row[5] or 0,
                "child_count": row[6] or 0
            })
        
        return families
    
    async def find_families_by_user_pattern(self, db: AsyncSession, *, username_pattern: str) -> List[Dict[str, Any]]:
        """Find families containing users matching a username pattern."""
        result = await db.execute(text("""
            SELECT DISTINCT
                f.id,
                f.name,
                f.invite_code,
                GROUP_CONCAT(u.username ORDER BY u.is_parent DESC, u.username) as members
            FROM families f
            JOIN users u ON u.family_id = f.id
            WHERE u.username LIKE :pattern
            GROUP BY f.id, f.name, f.invite_code
            ORDER BY f.name
        """), {"pattern": f"%{username_pattern}%"})
        
        families = []
        for row in result:
            families.append({
                "id": row[0],
                "name": row[1],
                "invite_code": row[2],
                "members": row[3].split(",") if row[3] else []
            })
        
        return families
    
    async def validate_family_access(self, db: AsyncSession, *, user_id: int, family_id: int) -> bool:
        """Validate that a user has access to a specific family."""
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.family_id == family_id
            )
        )
        return result.scalars().first() is not None
    
    async def get_user_family_context(self, db: AsyncSession, *, user_id: int) -> Optional[Family]:
        """Get the family context for a user - used for authentication middleware."""
        result = await db.execute(
            select(Family)
            .join(User, User.family_id == Family.id)
            .where(User.id == user_id)
        )
        return result.scalars().first()
    
    async def cleanup_expired_invite_codes(self, db: AsyncSession) -> int:
        """Clean up expired invite codes by generating new ones."""
        # Find families with expired invite codes
        result = await db.execute(
            select(Family.id).where(
                Family.invite_code_expires_at.isnot(None),
                Family.invite_code_expires_at < datetime.utcnow()
            )
        )
        
        expired_families = result.scalars().all()
        cleaned_count = 0
        
        for family_id in expired_families:
            # Generate new code without expiry
            await self.generate_new_invite_code(db, family_id=family_id, expires_in_days=None)
            cleaned_count += 1
        
        return cleaned_count