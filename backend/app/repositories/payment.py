from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import Payment
from .base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for payment operations."""
    
    async def get_by_child(self, db: AsyncSession, *, child_id: int) -> List[Payment]:
        """Get all payments for a specific child."""
        query = select(self.model).where(
            self.model.child_id == child_id
        ).order_by(self.model.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_payments_by_parent(self, db: AsyncSession, *, parent_id: int) -> List[Payment]:
        """Get all payments made by a specific parent."""
        query = select(self.model).where(
            self.model.parent_id == parent_id
        ).order_by(self.model.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_total_payments(self, db: AsyncSession, *, child_id: int) -> float:
        """Get total payments for a specific child (negative amounts)."""
        query = select(func.sum(self.model.amount)).where(
            self.model.child_id == child_id,
            self.model.is_adjustment == False
        )
        
        result = await db.execute(query)
        total = result.scalar_one_or_none()
        return total or 0.0
    
    async def get_total_adjustments(self, db: AsyncSession, *, child_id: int) -> float:
        """Get total adjustments for a specific child (can be positive or negative)."""
        query = select(func.sum(self.model.amount)).where(
            self.model.child_id == child_id,
            self.model.is_adjustment == True
        )
        
        result = await db.execute(query)
        total = result.scalar_one_or_none()
        return total or 0.0
    
    async def get_balance(self, db: AsyncSession, *, child_id: int) -> dict:
        """
        Calculate the current balance for a child.
        
        Returns a dictionary with:
        - total_payments: Sum of all payments (negative values)
        - total_adjustments: Sum of all adjustments (positive or negative)
        - total_earned: Not calculated here, needs to be provided from chore service
        - current_balance: Not calculated here, needs chore data
        """
        total_payments = await self.get_total_payments(db, child_id=child_id)
        total_adjustments = await self.get_total_adjustments(db, child_id=child_id)
        
        return {
            "total_payments": total_payments,
            "total_adjustments": total_adjustments
        }