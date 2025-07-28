"""
Enhanced Chore service with master pool, visibility, and recurrence support.
"""
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from .chore_service import ChoreService
from .chore_visibility_service import ChoreVisibilityService
from .recurrence_calculator import RecurrenceCalculator
from ..models.chore import Chore, RecurrenceType
from ..models.user import User
from ..schemas.chore import ChoreListResponse, ChoreWithAvailability


class ChoreServiceV2(ChoreService):
    """Enhanced chore service with V2 features."""
    
    def __init__(self):
        """Initialize enhanced chore service."""
        super().__init__()
        self.visibility_service = ChoreVisibilityService()
        self.recurrence_calculator = RecurrenceCalculator()
    
    async def get_pool_chores(
        self,
        db: AsyncSession,
        *,
        user: User
    ) -> ChoreListResponse:
        """
        Get master pool chores for a user with visibility and availability.
        
        For children:
        - Shows unassigned chores (assignee_id is None)
        - Filters out chores hidden from them
        - Shows completed recurring chores as grayed out until reset
        - Calculates availability progress
        
        For parents:
        - Shows all pool chores they created
        - No visibility filtering
        """
        if user.is_parent:
            # Parents see all pool chores they created
            stmt = select(Chore).where(
                and_(
                    Chore.creator_id == user.id,
                    Chore.assignee_id.is_(None),
                    Chore.is_disabled == False
                )
            )
        else:
            # Children see pool chores not hidden from them
            # First get hidden chore IDs
            hidden_chore_ids = await self.visibility_service.get_hidden_chore_ids_for_user(
                db, user.id
            )
            
            # Build query for pool chores
            conditions = [
                Chore.assignee_id.is_(None),
                Chore.is_disabled == False
            ]
            
            # Add visibility filter if any chores are hidden
            if hidden_chore_ids:
                conditions.append(~Chore.id.in_(hidden_chore_ids))
            
            stmt = select(Chore).where(and_(*conditions))
        
        # Execute query
        result = await db.execute(stmt)
        chores = list(result.scalars().all())
        
        # Process chores for availability
        available_chores = []
        completed_chores = []
        current_time = datetime.now(timezone.utc)
        
        for chore in chores:
            # Calculate availability
            is_available = True
            availability_progress = 100
            
            if chore.last_completion_time and chore.recurrence_type != RecurrenceType.NONE:
                # Calculate next available time
                next_available = self.recurrence_calculator.calculate_next_available_time(
                    chore.last_completion_time,
                    chore.recurrence_type,
                    chore.recurrence_value
                )
                
                if next_available:
                    is_available = self.recurrence_calculator.is_chore_available(
                        chore.last_completion_time,
                        next_available,
                        current_time
                    )
                    
                    availability_progress = self.recurrence_calculator.calculate_availability_progress(
                        chore.last_completion_time,
                        next_available,
                        current_time
                    )
                    
                    # Update chore's next_available_time if needed
                    if chore.next_available_time != next_available:
                        chore.next_available_time = next_available
                        await db.commit()
            
            # Create enhanced chore response
            chore_with_availability = ChoreWithAvailability(
                **chore.__dict__,
                is_available=is_available,
                availability_progress=availability_progress,
                is_hidden_from_current_user=False  # Already filtered out if hidden
            )
            
            if is_available:
                available_chores.append(chore_with_availability)
            else:
                completed_chores.append(chore_with_availability)
        
        return ChoreListResponse(
            available_chores=available_chores,
            completed_chores=completed_chores
        )
    
    async def claim_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        user_id: int
    ) -> Chore:
        """
        Claim an unassigned chore from the pool.
        
        Business rules:
        - Only children can claim chores
        - Chore must be unassigned
        - Chore must not be hidden from the user
        - Chore must be available (not in cooldown)
        """
        # Get user to verify they're a child
        user = await self.user_repo.get(db, id=user_id)
        if not user or user.is_parent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only children can claim chores"
            )
        
        # Get the chore
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # Check if already assigned
        if chore.assignee_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chore is already assigned"
            )
        
        # Check if chore is disabled
        if chore.is_disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot claim a disabled chore"
            )
        
        # Check visibility
        hidden_chore_ids = await self.visibility_service.get_hidden_chore_ids_for_user(
            db, user_id
        )
        if chore_id in hidden_chore_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot claim this chore"
            )
        
        # Check availability (recurrence)
        if chore.last_completion_time and chore.recurrence_type != RecurrenceType.NONE:
            next_available = self.recurrence_calculator.calculate_next_available_time(
                chore.last_completion_time,
                chore.recurrence_type,
                chore.recurrence_value
            )
            
            if next_available and not self.recurrence_calculator.is_chore_available(
                chore.last_completion_time,
                next_available
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chore is not yet available"
                )
        
        # Claim the chore
        updated_chore = await self.repository.update(
            db, id=chore_id, obj_in={"assignee_id": user_id}
        )
        
        return updated_chore
    
    async def complete_chore(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        user_id: int
    ) -> Chore:
        """
        Mark a chore as complete with recurrence support.
        
        Enhanced to:
        - Handle pool chores (claim if unassigned)
        - Update last_completion_time for recurrence
        - Calculate next_available_time
        """
        # Get the chore
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # If unassigned pool chore, claim it first
        if chore.assignee_id is None:
            chore = await self.claim_chore(db, chore_id=chore_id, user_id=user_id)
        elif chore.assignee_id != user_id:
            # Otherwise verify user is assignee
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the assignee of this chore"
            )
        
        # Check if chore is disabled
        if chore.is_disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot complete a disabled chore"
            )
        
        # Check availability for recurring chores
        if chore.is_completed and chore.recurrence_type != RecurrenceType.NONE:
            if chore.last_completion_time:
                next_available = self.recurrence_calculator.calculate_next_available_time(
                    chore.last_completion_time,
                    chore.recurrence_type,
                    chore.recurrence_value
                )
                
                if next_available and not self.recurrence_calculator.is_chore_available(
                    chore.last_completion_time,
                    next_available
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Chore is not yet available for completion"
                    )
            
            # Reset the chore for re-completion
            await self.repository.reset_chore(db, chore_id=chore_id)
            chore = await self.get(db, id=chore_id)
        
        # Mark as completed
        completion_time = datetime.now(timezone.utc)
        update_data = {
            "is_completed": True,
            "completion_date": completion_time,
            "last_completion_time": completion_time
        }
        
        # Calculate next available time for recurring chores
        if chore.recurrence_type != RecurrenceType.NONE:
            next_available = self.recurrence_calculator.calculate_next_available_time(
                completion_time,
                chore.recurrence_type,
                chore.recurrence_value
            )
            update_data["next_available_time"] = next_available
        
        updated_chore = await self.repository.update(
            db, id=chore_id, obj_in=update_data
        )
        
        return updated_chore
    
    async def create_chore_with_visibility(
        self,
        db: AsyncSession,
        *,
        creator_id: int,
        chore_data: Dict[str, Any],
        hidden_from_users: Optional[List[int]] = None
    ) -> Chore:
        """
        Create a chore with visibility settings.
        
        Args:
            creator_id: ID of parent creating the chore
            chore_data: Chore creation data
            hidden_from_users: List of user IDs to hide the chore from
        """
        # Remove hidden_from_users from chore_data if present
        if "hidden_from_users" in chore_data:
            hidden_from_users = chore_data.pop("hidden_from_users")
        
        # Create the chore using parent method
        chore = await self.create_chore(
            db,
            creator_id=creator_id,
            chore_data=chore_data
        )
        
        # Set visibility if specified
        if hidden_from_users:
            creator_user = await self.user_repo.get(db, id=creator_id)
            for user_id in hidden_from_users:
                await self.visibility_service.update_chore_visibility(
                    db,
                    chore_id=chore.id,
                    user_id=user_id,
                    is_hidden=True,
                    current_user=creator_user
                )
        
        return chore
    
    async def get_chore_with_availability(
        self,
        db: AsyncSession,
        *,
        chore_id: int,
        user_id: int
    ) -> ChoreWithAvailability:
        """
        Get a single chore with availability information.
        
        Args:
            chore_id: ID of the chore
            user_id: ID of the requesting user
        """
        chore = await self.get(db, id=chore_id)
        if not chore:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chore not found"
            )
        
        # Check if hidden from user
        user = await self.user_repo.get(db, id=user_id)
        is_hidden = False
        
        if not user.is_parent:
            hidden_chore_ids = await self.visibility_service.get_hidden_chore_ids_for_user(
                db, user_id
            )
            is_hidden = chore_id in hidden_chore_ids
        
        # Calculate availability
        is_available = True
        availability_progress = 100
        
        if chore.last_completion_time and chore.recurrence_type != RecurrenceType.NONE:
            next_available = self.recurrence_calculator.calculate_next_available_time(
                chore.last_completion_time,
                chore.recurrence_type,
                chore.recurrence_value
            )
            
            if next_available:
                is_available = self.recurrence_calculator.is_chore_available(
                    chore.last_completion_time,
                    next_available
                )
                
                availability_progress = self.recurrence_calculator.calculate_availability_progress(
                    chore.last_completion_time,
                    next_available
                )
        
        return ChoreWithAvailability(
            **chore.__dict__,
            is_available=is_available,
            availability_progress=availability_progress,
            is_hidden_from_current_user=is_hidden
        )