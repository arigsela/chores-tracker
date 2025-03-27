from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, extract, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.chore import Chore

class ChoreRepository(BaseRepository[Chore]):
    def __init__(self):
        super().__init__(Chore)
    
    async def get_by_assignee(self, db: AsyncSession, *, assignee_id: int) -> List[Chore]:
        """Get all chores for an assignee."""
        print(f"Fetching chores for assignee ID: {assignee_id}")
        result = await db.execute(
            select(Chore)
            .where(
                Chore.assignee_id == assignee_id
            )
            .options(joinedload(Chore.assignee), joinedload(Chore.creator))
        )
        chores = result.scalars().all()
        print(f"Found {len(chores)} chores for assignee ID: {assignee_id}")
        for chore in chores:
            print(f"Chore: {chore.id}, {chore.title}, completed: {chore.is_completed}, approved: {chore.is_approved}")
        return chores
    
    async def get_available_for_assignee(self, db: AsyncSession, *, assignee_id: int) -> List[Chore]:
        """Get available chores for an assignee (not completed or past cooldown period)."""
        now = datetime.now()
        
        # Query all chores for the assignee, excluding disabled ones
        query = select(Chore).where(
            and_(
                Chore.assignee_id == assignee_id,
                Chore.is_disabled == False
            )
        )
        
        # Filter to only show chores that are either:
        # 1) Not completed OR
        # 2) Completed but not approved and past their cooldown period
        result = await db.execute(
            query.where(
                or_(
                    Chore.is_completed == False,  # Not completed
                    and_(
                        Chore.is_completed == True,
                        Chore.is_approved == False,
                        Chore.completion_date <= (now - timedelta(days=1))  # At least 1 day old as a fallback
                    )
                )
            )
            .options(joinedload(Chore.assignee), joinedload(Chore.creator))
        )
        
        # Get the initial list of chores
        chores = result.scalars().all()
        
        # Filter the chores that are in cooldown period more precisely
        filtered_chores = []
        for chore in chores:
            if not chore.is_completed:
                # Not completed chores are always available
                filtered_chores.append(chore)
            elif chore.completion_date and chore.cooldown_days > 0:
                # Check if past cooldown period
                cooldown_end = chore.completion_date + timedelta(days=chore.cooldown_days)
                if now >= cooldown_end:
                    filtered_chores.append(chore)
            else:
                # No cooldown or completion date, so include it
                filtered_chores.append(chore)
                
        return filtered_chores
    
    async def get_by_creator(self, db: AsyncSession, *, creator_id: int) -> List[Chore]:
        """Get all chores created by a user."""
        result = await db.execute(
            select(Chore)
            .where(Chore.creator_id == creator_id)
            .options(joinedload(Chore.assignee), joinedload(Chore.creator))
        )
        return result.scalars().all()
    
    async def get_pending_approval(self, db: AsyncSession, *, creator_id: int) -> List[Chore]:
        """Get all completed but unapproved chores for a parent."""
        print(f"Fetching pending approval chores for creator ID: {creator_id}")
        result = await db.execute(
            select(Chore)
            .where(
                and_(
                    Chore.creator_id == creator_id,
                    Chore.is_completed == True, 
                    Chore.is_approved == False
                )
            )
            .options(joinedload(Chore.assignee), joinedload(Chore.creator))
        )
        chores = result.scalars().all()
        print(f"Found {len(chores)} pending approval chores for creator ID: {creator_id}")
        for chore in chores:
            print(f"Pending chore: {chore.id}, {chore.title}, completed: {chore.is_completed}, approved: {chore.is_approved}")
        return chores
    
    async def get_pending_approval_for_child(self, db: AsyncSession, *, assignee_id: int) -> List[Chore]:
        """Get all completed but unapproved chores for a specific child."""
        result = await db.execute(
            select(Chore)
            .where(
                and_(
                    Chore.assignee_id == assignee_id,
                    Chore.is_completed == True, 
                    Chore.is_approved == False
                )
            )
            .options(joinedload(Chore.assignee), joinedload(Chore.creator))
        )
        return result.scalars().all()
    
    async def get_completed_by_child(self, db: AsyncSession, *, child_id: int) -> List[Chore]:
        """Get all completed chores for a specific child."""
        result = await db.execute(
            select(Chore)
            .where(
                and_(
                    Chore.assignee_id == child_id,
                    Chore.is_completed == True
                )
            )
            .options(joinedload(Chore.assignee), joinedload(Chore.creator))
        )
        return result.scalars().all()
    
    async def mark_completed(self, db: AsyncSession, *, chore_id: int) -> Optional[Chore]:
        """Mark a chore as completed."""
        now = datetime.now()
        return await self.update(
            db, 
            id=chore_id, 
            obj_in={
                "is_completed": True,
                "completion_date": now
            }
        )
    
    async def approve_chore(self, db: AsyncSession, *, chore_id: int, reward_value: Optional[float] = None) -> Optional[Chore]:
        """Approve a completed chore with optional custom reward value."""
        update_data = {"is_approved": True}
        
        # Get the chore first to access its current reward value
        chore = await self.get(db, id=chore_id)
        if not chore:
            print(f"Error: Could not find chore with ID {chore_id}")
            return None
        
        print(f"Approving chore ID {chore_id}: Current reward = {chore.reward}, Provided reward_value = {reward_value}")
        
        # If reward value is provided, update the reward
        if reward_value is not None:
            print(f"Using provided reward value: {reward_value}")
            update_data["reward"] = reward_value
        # For fixed reward chores, ensure we preserve the reward value
        elif not chore.is_range_reward and chore.reward is not None:
            # Always explicitly set the reward value to avoid any issues with nulls
            print(f"Using existing reward value: {chore.reward}")
            update_data["reward"] = chore.reward
        else:
            print(f"Warning: No reward value provided for chore ID {chore_id}")
            # Default to 0 if no reward value is available
            update_data["reward"] = 0.0
        
        print(f"Final update data: {update_data}")
        updated_chore = await self.update(db, id=chore_id, obj_in=update_data)
        
        # Double-check the result
        if updated_chore:
            print(f"Chore {chore_id} approved with reward = {updated_chore.reward}")
        else:
            print(f"Error: Failed to update chore {chore_id}")
            
        return updated_chore
    
    async def disable_chore(self, db: AsyncSession, *, chore_id: int) -> Optional[Chore]:
        """Disable a chore."""
        return await self.update(
            db, 
            id=chore_id, 
            obj_in={
                "is_disabled": True
            }
        )
    
    async def reset_chore(self, db: AsyncSession, *, chore_id: int) -> Optional[Chore]:
        """Reset a chore to uncompleted state."""
        return await self.update(
            db, 
            id=chore_id, 
            obj_in={
                "is_completed": False,
                "is_approved": False,
                "completion_date": None
            }
        )
    
    async def enable_chore(self, db: AsyncSession, *, chore_id: int) -> Optional[Chore]:
        """Enable a previously disabled chore."""
        return await self.update(
            db, 
            id=chore_id, 
            obj_in={
                "is_disabled": False
            }
        )
    
    async def reset_disabled_chores(self, db: AsyncSession) -> int:
        """Reset chores that might have been partially disabled with old implementation.
        Returns the number of fixed chores."""
        
        # Find chores that were marked as completed and approved without being properly disabled
        result = await db.execute(
            select(Chore)
            .where(
                and_(
                    Chore.is_completed == True,
                    Chore.is_approved == True,
                    Chore.is_disabled == False,
                    # Filter out chores with real rewards (likely actual completed chores)
                    Chore.reward <= 0.01
                )
            )
        )
        chores = result.scalars().all()
        
        fixed_count = 0
        for chore in chores:
            # Set them as properly disabled and reset completion/approval status
            await self.update(
                db,
                id=chore.id,
                obj_in={
                    "is_disabled": True,
                    "is_completed": False,
                    "is_approved": False,
                    "completion_date": None
                }
            )
            fixed_count += 1
            
        return fixed_count