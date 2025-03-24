from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models.chore import Chore

class ChoreRepository(BaseRepository[Chore]):
    def __init__(self):
        super().__init__(Chore)
    
    async def get_by_assignee(self, db: AsyncSession, *, assignee_id: int) -> List[Chore]:
        """Get all chores for an assignee."""
        result = await db.execute(select(Chore).where(Chore.assignee_id == assignee_id))
        return result.scalars().all()
    
    async def get_by_creator(self, db: AsyncSession, *, creator_id: int) -> List[Chore]:
        """Get all chores created by a user."""
        result = await db.execute(select(Chore).where(Chore.creator_id == creator_id))
        return result.scalars().all()
    
    async def get_completed_unapproved(self, db: AsyncSession) -> List[Chore]:
        """Get all completed but unapproved chores."""
        result = await db.execute(
            select(Chore).where(
                and_(Chore.is_completed == True, Chore.is_approved == False)
            )
        )
        return result.scalars().all()
    
    async def mark_completed(self, db: AsyncSession, *, chore_id: int) -> Optional[Chore]:
        """Mark a chore as completed."""
        return await self.update(db, id=chore_id, obj_in={"is_completed": True})
    
    async def approve_chore(self, db: AsyncSession, *, chore_id: int) -> Optional[Chore]:
        """Approve a completed chore."""
        return await self.update(db, id=chore_id, obj_in={"is_approved": True})