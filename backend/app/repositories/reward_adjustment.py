from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .base import BaseRepository
from ..models.reward_adjustment import RewardAdjustment

class RewardAdjustmentRepository(BaseRepository[RewardAdjustment]):
    def __init__(self):
        super().__init__(RewardAdjustment)
    
    async def get_by_child_id(
        self, db: AsyncSession, *, child_id: int, skip: int = 0, limit: int = 100
    ) -> List[RewardAdjustment]:
        """Get all adjustments for a specific child."""
        result = await db.execute(
            select(RewardAdjustment)
            .where(RewardAdjustment.child_id == child_id)
            .order_by(RewardAdjustment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_parent_id(
        self, db: AsyncSession, *, parent_id: int, skip: int = 0, limit: int = 100
    ) -> List[RewardAdjustment]:
        """Get all adjustments created by a specific parent."""
        result = await db.execute(
            select(RewardAdjustment)
            .where(RewardAdjustment.parent_id == parent_id)
            .order_by(RewardAdjustment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def calculate_total_adjustments(
        self, db: AsyncSession, *, child_id: int
    ) -> Decimal:
        """Calculate the sum of all adjustments for a child."""
        result = await db.execute(
            select(func.coalesce(func.sum(RewardAdjustment.amount), 0))
            .where(RewardAdjustment.child_id == child_id)
        )
        total = result.scalar()
        return Decimal(str(total))
    
    async def get_with_relationships(
        self, db: AsyncSession, *, adjustment_id: int
    ) -> Optional[RewardAdjustment]:
        """Get an adjustment with child and parent relationships loaded."""
        result = await db.execute(
            select(RewardAdjustment)
            .options(
                joinedload(RewardAdjustment.child),
                joinedload(RewardAdjustment.parent)
            )
            .where(RewardAdjustment.id == adjustment_id)
        )
        return result.scalars().first()
    
    async def get_by_parent(
        self, db: AsyncSession, *, parent_id: int, skip: int = 0, limit: int = 100
    ) -> List[RewardAdjustment]:
        """Alias for get_by_parent_id - get all adjustments created by a parent."""
        return await self.get_by_parent_id(db, parent_id=parent_id, skip=skip, limit=limit)
    
    async def get_adjustment_count(
        self, db: AsyncSession, *, child_id: int
    ) -> int:
        """Get the count of adjustments for a specific child."""
        result = await db.execute(
            select(func.count(RewardAdjustment.id))
            .where(RewardAdjustment.child_id == child_id)
        )
        return result.scalar() or 0