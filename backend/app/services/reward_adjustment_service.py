"""
Reward adjustment service with business logic for reward adjustment operations.
"""
from typing import List, Optional
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ..models.user import User
from ..models.reward_adjustment import RewardAdjustment
from ..repositories.reward_adjustment import RewardAdjustmentRepository
from ..repositories.user import UserRepository
from ..schemas.reward_adjustment import RewardAdjustmentCreate


class RewardAdjustmentService(BaseService[RewardAdjustment, RewardAdjustmentRepository]):
    """Service for reward adjustment business logic."""
    
    def __init__(self):
        """Initialize reward adjustment service."""
        super().__init__(RewardAdjustmentRepository())
        self.user_repository = UserRepository()
    
    async def create_adjustment(
        self,
        db: AsyncSession,
        *,
        adjustment_data: RewardAdjustmentCreate,
        current_user_id: int
    ) -> RewardAdjustment:
        """
        Create a new reward adjustment.
        
        Business rules:
        - Only parents can create adjustments
        - Parent can only adjust their own children's rewards
        - Amount must be non-zero
        - Reason is required
        """
        # Get current user and validate they're a parent
        current_user = await self.user_repository.get(db, id=current_user_id)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current user not found"
            )
        
        if not current_user.is_parent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only parents can create reward adjustments"
            )
        
        # Get child and validate relationship
        child = await self.user_repository.get(db, id=adjustment_data.child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child user not found"
            )
        
        if child.parent_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only adjust rewards for your own children"
            )
        
        # Check for negative balance if this is a penalty
        if adjustment_data.amount < 0:
            current_balance = await self.repository.calculate_total_adjustments(
                db, child_id=child.id
            )
            if current_balance + adjustment_data.amount < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Adjustment would result in negative balance. Current balance: ${current_balance}"
                )
        
        # Create the adjustment
        adjustment_dict = adjustment_data.model_dump()
        adjustment_dict['parent_id'] = current_user_id
        
        return await self.repository.create(db, obj_in=adjustment_dict)
    
    async def get_child_adjustments(
        self,
        db: AsyncSession,
        *,
        child_id: int,
        current_user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[RewardAdjustment]:
        """
        Get all adjustments for a specific child.
        
        Business rules:
        - Parents can view adjustments for their own children
        - Children cannot view their own adjustments (in MVP)
        """
        # Get current user
        current_user = await self.user_repository.get(db, id=current_user_id)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current user not found"
            )
        
        # Get child
        child = await self.user_repository.get(db, id=child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child user not found"
            )
        
        # Validate permissions
        if current_user.is_parent:
            # Parents can only view their own children's adjustments
            if child.parent_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view adjustments for your own children"
                )
        else:
            # Children cannot view adjustments in MVP
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Children cannot view reward adjustments"
            )
        
        return await self.repository.get_by_child_id(
            db,
            child_id=child_id,
            skip=skip,
            limit=limit
        )
    
    async def get_parent_adjustments(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        current_user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[RewardAdjustment]:
        """
        Get all adjustments created by a specific parent.
        
        Business rules:
        - Parents can only view their own created adjustments
        """
        # Validate the requesting user is the parent
        if parent_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own created adjustments"
            )
        
        current_user = await self.user_repository.get(db, id=current_user_id)
        if not current_user or not current_user.is_parent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only parents can view adjustments"
            )
        
        return await self.repository.get_by_parent_id(
            db,
            parent_id=parent_id,
            skip=skip,
            limit=limit
        )
    
    async def get_total_adjustments(
        self,
        db: AsyncSession,
        *,
        child_id: int,
        current_user_id: int
    ) -> Decimal:
        """
        Get the total sum of adjustments for a child.
        
        Business rules:
        - Parents can view totals for their own children
        - Used internally for balance calculations
        """
        # Get current user
        current_user = await self.user_repository.get(db, id=current_user_id)
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current user not found"
            )
        
        # Get child
        child = await self.user_repository.get(db, id=child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child user not found"
            )
        
        # Validate permissions
        if current_user.is_parent and child.parent_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view totals for your own children"
            )
        elif not current_user.is_parent and child_id != current_user_id:
            # Allow children to see their own total (for balance calculation)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own adjustment total"
            )
        
        return await self.repository.calculate_total_adjustments(db, child_id=child_id)