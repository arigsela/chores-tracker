"""Service for managing chore visibility settings."""
from typing import List, Optional, Set
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.chore_visibility import ChoreVisibility
from ..models.user import User
from ..schemas.chore_visibility import (
    ChoreVisibilityCreate,
    ChoreVisibilityUpdate,
    ChoreVisibilityBulkUpdate
)


class ChoreVisibilityService:
    """Service for managing chore visibility."""
    
    async def update_chore_visibility(
        self,
        db: AsyncSession,
        chore_id: int,
        user_id: int,
        is_hidden: bool,
        current_user: User
    ) -> ChoreVisibility:
        """
        Update visibility setting for a specific chore and user.
        
        Args:
            db: Database session
            chore_id: ID of the chore
            user_id: ID of the user to update visibility for
            is_hidden: Whether to hide the chore from the user
            current_user: The user making the request (must be parent)
            
        Returns:
            Updated or created ChoreVisibility record
            
        Raises:
            PermissionError: If current user is not a parent
        """
        # Check permissions - only parents can manage visibility
        if not current_user.is_parent:
            raise PermissionError("Only parents can manage chore visibility")
        
        # Check if visibility record exists
        stmt = select(ChoreVisibility).where(
            ChoreVisibility.chore_id == chore_id,
            ChoreVisibility.user_id == user_id
        )
        result = await db.execute(stmt)
        visibility = result.scalar_one_or_none()
        
        if visibility:
            # Update existing record
            visibility.is_hidden = is_hidden
            await db.commit()
            await db.refresh(visibility)
            return visibility
        else:
            # Create new record
            visibility = ChoreVisibility(
                chore_id=chore_id,
                user_id=user_id,
                is_hidden=is_hidden
            )
            db.add(visibility)
            await db.commit()
            await db.refresh(visibility)
            return visibility
    
    async def get_hidden_chore_ids_for_user(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Set[int]:
        """
        Get all chore IDs that are hidden from a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Set of chore IDs that are hidden from the user
        """
        stmt = select(ChoreVisibility.chore_id).where(
            ChoreVisibility.user_id == user_id,
            ChoreVisibility.is_hidden == True
        )
        result = await db.execute(stmt)
        return set(result.scalars().all())
    
    async def bulk_update_visibility(
        self,
        db: AsyncSession,
        bulk_update: ChoreVisibilityBulkUpdate,
        current_user: User
    ) -> List[ChoreVisibility]:
        """
        Bulk update visibility settings for a chore.
        
        Args:
            db: Database session
            bulk_update: Bulk update request with chore_id and user lists
            current_user: The user making the request (must be parent)
            
        Returns:
            List of updated/created ChoreVisibility records
            
        Raises:
            PermissionError: If current user is not a parent
        """
        # Check permissions
        if not current_user.is_parent:
            raise PermissionError("Only parents can manage chore visibility")
        
        updated_records = []
        
        # Process users to hide chore from
        for user_id in bulk_update.hidden_from_users:
            record = await self.update_chore_visibility(
                db, bulk_update.chore_id, user_id, True, current_user
            )
            updated_records.append(record)
        
        # Process users to show chore to
        for user_id in bulk_update.visible_to_users:
            record = await self.update_chore_visibility(
                db, bulk_update.chore_id, user_id, False, current_user
            )
            updated_records.append(record)
        
        return updated_records
    
    async def delete_chore_visibility_settings(
        self,
        db: AsyncSession,
        chore_id: int
    ) -> None:
        """
        Delete all visibility settings for a chore.
        
        Args:
            db: Database session
            chore_id: ID of the chore
        """
        stmt = delete(ChoreVisibility).where(ChoreVisibility.chore_id == chore_id)
        await db.execute(stmt)
        await db.commit()
    
    async def get_chore_visibility_settings(
        self,
        db: AsyncSession,
        chore_id: int
    ) -> List[ChoreVisibility]:
        """
        Get all visibility settings for a chore.
        
        Args:
            db: Database session
            chore_id: ID of the chore
            
        Returns:
            List of ChoreVisibility records for the chore
        """
        stmt = select(ChoreVisibility).where(ChoreVisibility.chore_id == chore_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())