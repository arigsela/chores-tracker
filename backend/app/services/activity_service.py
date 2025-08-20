"""
Activity service for managing activity logging and retrieval.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ..models.activity import Activity
from ..repositories.activity import ActivityRepository


class ActivityService(BaseService[Activity, ActivityRepository]):
    """Service for activity-related business logic."""
    
    def __init__(self):
        """Initialize activity service."""
        super().__init__(ActivityRepository())
    
    async def log_chore_completed(
        self,
        db: AsyncSession,
        *,
        child_id: int,
        chore_id: int,
        chore_title: str
    ) -> Activity:
        """
        Log when a child completes a chore.
        
        Args:
            db: Database session
            child_id: ID of child who completed the chore
            chore_id: ID of the completed chore
            chore_title: Title of the completed chore
            
        Returns:
            Created activity record
        """
        description = f"Completed chore: {chore_title}"
        activity_data = {
            "chore_id": chore_id,
            "chore_title": chore_title
        }
        
        return await self.repository.create_activity(
            db,
            user_id=child_id,
            activity_type="chore_completed",
            description=description,
            activity_data=activity_data
        )
    
    async def log_chore_approved(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int,
        chore_id: int,
        chore_title: str,
        reward_amount: float
    ) -> Activity:
        """
        Log when a parent approves a chore.
        
        Args:
            db: Database session
            parent_id: ID of parent who approved the chore
            child_id: ID of child whose chore was approved
            chore_id: ID of the approved chore
            chore_title: Title of the approved chore
            reward_amount: Amount of reward earned
            
        Returns:
            Created activity record
        """
        description = f"Approved chore '{chore_title}' for ${reward_amount:.2f}"
        activity_data = {
            "chore_id": chore_id,
            "chore_title": chore_title,
            "reward_amount": reward_amount
        }
        
        return await self.repository.create_activity(
            db,
            user_id=parent_id,
            activity_type="chore_approved",
            description=description,
            target_user_id=child_id,
            activity_data=activity_data
        )
    
    async def log_chore_rejected(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int,
        chore_id: int,
        chore_title: str,
        rejection_reason: str
    ) -> Activity:
        """
        Log when a parent rejects a chore.
        
        Args:
            db: Database session
            parent_id: ID of parent who rejected the chore
            child_id: ID of child whose chore was rejected
            chore_id: ID of the rejected chore
            chore_title: Title of the rejected chore
            rejection_reason: Reason for rejection
            
        Returns:
            Created activity record
        """
        description = f"Rejected chore '{chore_title}': {rejection_reason[:50]}{'...' if len(rejection_reason) > 50 else ''}"
        activity_data = {
            "chore_id": chore_id,
            "chore_title": chore_title,
            "rejection_reason": rejection_reason
        }
        
        return await self.repository.create_activity(
            db,
            user_id=parent_id,
            activity_type="chore_rejected",
            description=description,
            target_user_id=child_id,
            activity_data=activity_data
        )
    
    async def log_adjustment_applied(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int,
        adjustment_id: int,
        amount: float,
        reason: str,
        adjustment_type: str = "adjustment"
    ) -> Activity:
        """
        Log when a parent applies a reward adjustment.
        
        Args:
            db: Database session
            parent_id: ID of parent who applied the adjustment
            child_id: ID of child receiving the adjustment
            adjustment_id: ID of the adjustment record
            amount: Amount of the adjustment (positive or negative)
            reason: Reason for the adjustment
            adjustment_type: Type of adjustment (bonus, deduction, etc.)
            
        Returns:
            Created activity record
        """
        if amount >= 0:
            description = f"Applied bonus of ${amount:.2f}: {reason[:50]}{'...' if len(reason) > 50 else ''}"
        else:
            description = f"Applied deduction of ${abs(amount):.2f}: {reason[:50]}{'...' if len(reason) > 50 else ''}"
        
        activity_data = {
            "adjustment_id": adjustment_id,
            "amount": amount,
            "reason": reason,
            "adjustment_type": adjustment_type
        }
        
        return await self.repository.create_activity(
            db,
            user_id=parent_id,
            activity_type="adjustment_applied",
            description=description,
            target_user_id=child_id,
            activity_data=activity_data
        )
    
    async def log_chore_created(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: Optional[int],
        chore_id: int,
        chore_title: str,
        reward_amount: Optional[float] = None
    ) -> Activity:
        """
        Log when a parent creates a new chore.
        
        Args:
            db: Database session
            parent_id: ID of parent who created the chore
            child_id: ID of child assigned to chore (if any)
            chore_id: ID of the created chore
            chore_title: Title of the created chore
            reward_amount: Reward amount (if fixed reward)
            
        Returns:
            Created activity record
        """
        if child_id:
            description = f"Created chore '{chore_title}'"
            if reward_amount:
                description += f" (${reward_amount:.2f})"
        else:
            description = f"Created unassigned chore '{chore_title}'"
        
        activity_data = {
            "chore_id": chore_id,
            "chore_title": chore_title,
            "reward_amount": reward_amount
        }
        
        return await self.repository.create_activity(
            db,
            user_id=parent_id,
            activity_type="chore_created",
            description=description,
            target_user_id=child_id,
            activity_data=activity_data
        )
    
    async def get_recent_activities_for_family(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        limit: int = 20
    ) -> List[Activity]:
        """
        Get recent activities for parent and all their children.
        
        Args:
            db: Database session
            parent_id: ID of the parent user
            limit: Maximum number of activities to return
            
        Returns:
            List of recent family activities
        """
        return await self.repository.get_family_activities(
            db, parent_id=parent_id, limit=limit
        )
    
    async def get_recent_activities_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        limit: int = 20
    ) -> List[Activity]:
        """
        Get recent activities for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of activities to return
            
        Returns:
            List of recent user activities
        """
        return await self.repository.get_recent_activities(
            db, user_id=user_id, limit=limit
        )
    
    async def get_activity_summary(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, int]:
        """
        Get activity summary with counts by type.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter activities
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with activity type counts
        """
        return await self.repository.get_activity_counts_by_type(
            db, user_id=user_id, days_back=days_back
        )