"""
Activity repository for database operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.activity import Activity


class ActivityRepository(BaseRepository[Activity]):
    """Repository for Activity database operations."""
    
    def __init__(self):
        """Initialize Activity repository."""
        super().__init__(Activity)
    
    async def get_recent_activities(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Activity]:
        """
        Get recent activities, optionally filtered by user.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter activities
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            
        Returns:
            List of activities ordered by creation time (newest first)
        """
        query = select(self.model).options(
            selectinload(Activity.user),
            selectinload(Activity.target_user)
        ).order_by(desc(Activity.created_at)).limit(limit).offset(offset)
        
        if user_id:
            query = query.where(Activity.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_activities_by_type(
        self,
        db: AsyncSession,
        *,
        activity_type: str,
        user_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Activity]:
        """
        Get activities filtered by type.
        
        Args:
            db: Database session
            activity_type: Type of activity to filter
            user_id: Optional user ID to filter activities
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            
        Returns:
            List of activities of specified type
        """
        query = select(self.model).options(
            selectinload(Activity.user),
            selectinload(Activity.target_user)
        ).where(
            Activity.activity_type == activity_type
        ).order_by(desc(Activity.created_at)).limit(limit).offset(offset)
        
        if user_id:
            query = query.where(Activity.user_id == user_id)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_family_activities(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Activity]:
        """
        Get activities for a parent and all their children.
        
        Args:
            db: Database session
            parent_id: ID of the parent user
            limit: Maximum number of activities to return
            offset: Number of activities to skip
            
        Returns:
            List of activities for the entire family
        """
        from ..models.user import User
        
        # Get all child IDs for this parent
        children_query = select(User.id).where(User.parent_id == parent_id)
        children_result = await db.execute(children_query)
        child_ids = children_result.scalars().all()
        
        # Include parent ID in the list
        family_ids = [parent_id] + child_ids
        
        query = select(self.model).options(
            selectinload(Activity.user),
            selectinload(Activity.target_user)
        ).where(
            Activity.user_id.in_(family_ids) | 
            Activity.target_user_id.in_(family_ids)
        ).order_by(desc(Activity.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create_activity(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        activity_type: str,
        description: str,
        target_user_id: Optional[int] = None,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> Activity:
        """
        Create a new activity record.
        
        Args:
            db: Database session
            user_id: ID of user performing the activity
            activity_type: Type of activity (e.g., 'chore_completed')
            description: Human-readable description
            target_user_id: Optional target user ID
            activity_data: Optional activity-specific data
            
        Returns:
            Created activity record
        """
        activity_in = {
            "user_id": user_id,
            "activity_type": activity_type,
            "description": description,
            "target_user_id": target_user_id,
            "activity_data": activity_data or {},
            "created_at": datetime.utcnow()
        }
        
        return await self.create(db, obj_in=activity_in)
    
    async def get_activity_counts_by_type(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, int]:
        """
        Get activity counts grouped by type for recent period.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter activities
            days_back: Number of days to look back
            
        Returns:
            Dictionary mapping activity types to counts
        """
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = select(
            Activity.activity_type,
            func.count(Activity.id).label('count')
        ).where(
            Activity.created_at >= cutoff_date
        ).group_by(Activity.activity_type)
        
        if user_id:
            query = query.where(Activity.user_id == user_id)
        
        result = await db.execute(query)
        return {row.activity_type: row.count for row in result.all()}