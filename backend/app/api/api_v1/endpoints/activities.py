"""
Activity endpoints for retrieving activity feed and statistics.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy import select

from ....dependencies.auth import get_current_user
from ....models.user import User
from ....services.activity_service import ActivityService
from ....schemas.activity import (
    ActivityResponse, 
    ActivityListResponse, 
    ActivitySummaryResponse,
    ActivityTypes
)
from ....db.base import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
activity_service = ActivityService()


@router.get("/recent", response_model=ActivityListResponse)
async def get_recent_activities(
    limit: int = Query(default=20, ge=1, le=100, description="Number of activities to return"),
    offset: int = Query(default=0, ge=0, description="Number of activities to skip"),
    activity_type: Optional[str] = Query(
        default=None,
        description=f"Filter by activity type. Options: {', '.join(ActivityTypes.get_all_types())}"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityListResponse:
    """
    Get recent activities for the current user.
    
    - **Parents**: See activities for themselves and all their children
    - **Children**: See only their own activities
    - **Filtering**: Optionally filter by activity type
    - **Pagination**: Use limit and offset for pagination
    """
    try:
        if current_user.is_parent:
            # Parents see family-wide activities
            if activity_type:
                # For type filtering, get user activities first then filter
                activities = await activity_service.repository.get_activities_by_type(
                    db, 
                    activity_type=activity_type,
                    limit=limit,
                    offset=offset
                )
                # Filter to only include family members
                from ....models.user import User as UserModel
                from sqlalchemy import select
                children_query = select(UserModel.id).where(UserModel.parent_id == current_user.id)
                children_result = await db.execute(children_query)
                child_ids = children_result.scalars().all()
                family_ids = [current_user.id] + child_ids
                
                activities = [
                    activity for activity in activities 
                    if activity.user_id in family_ids or 
                    (activity.target_user_id and activity.target_user_id in family_ids)
                ]
            else:
                activities = await activity_service.get_recent_activities_for_family(
                    db, parent_id=current_user.id, limit=limit
                )
        else:
            # Children see only their own activities
            if activity_type:
                activities = await activity_service.repository.get_activities_by_type(
                    db,
                    activity_type=activity_type,
                    user_id=current_user.id,
                    limit=limit,
                    offset=offset
                )
            else:
                activities = await activity_service.get_recent_activities_for_user(
                    db, user_id=current_user.id, limit=limit
                )
        
        return ActivityListResponse(
            activities=activities,
            has_more=len(activities) == limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activities: {str(e)}"
        )


@router.get("/summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    days_back: int = Query(
        default=30, 
        ge=1, 
        le=365, 
        description="Number of days to analyze"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivitySummaryResponse:
    """
    Get activity summary statistics for the current user.
    
    - **Parents**: See statistics for entire family
    - **Children**: See only their own statistics
    - **Period**: Configurable analysis period (1-365 days)
    """
    try:
        if current_user.is_parent:
            # For parents, we need to aggregate across the family
            # First get all child IDs
            from ....models.user import User as UserModel
            children_query = select(UserModel.id).where(UserModel.parent_id == current_user.id)
            children_result = await db.execute(children_query)
            child_ids = children_result.scalars().all()
            
            # Get activity counts for each family member and aggregate
            family_ids = [current_user.id] + child_ids
            all_counts = {}
            
            for user_id in family_ids:
                user_counts = await activity_service.get_activity_summary(
                    db, user_id=user_id, days_back=days_back
                )
                for activity_type, count in user_counts.items():
                    all_counts[activity_type] = all_counts.get(activity_type, 0) + count
            
            activity_counts = all_counts
        else:
            # Children see only their own statistics
            activity_counts = await activity_service.get_activity_summary(
                db, user_id=current_user.id, days_back=days_back
            )
        
        total_activities = sum(activity_counts.values())
        
        return ActivitySummaryResponse(
            activity_counts=activity_counts,
            total_activities=total_activities,
            period_days=days_back
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity summary: {str(e)}"
        )


@router.get("/types", response_model=dict)
async def get_activity_types(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get available activity types and their descriptions.
    
    Useful for frontend filtering and display purposes.
    """
    return {
        "activity_types": ActivityTypes.get_all_types(),
        "descriptions": ActivityTypes.get_type_descriptions()
    }


@router.get("/debug", response_model=dict)
async def debug_activities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Debug endpoint to help troubleshoot activity feed issues.
    """
    try:
        # Get basic user info
        user_info = {
            "id": current_user.id,
            "username": current_user.username,
            "is_parent": current_user.is_parent,
            "email": current_user.email
        }
        
        # Try to get activities
        if current_user.is_parent:
            activities = await activity_service.get_recent_activities_for_family(
                db, parent_id=current_user.id, limit=5
            )
        else:
            activities = await activity_service.get_recent_activities_for_user(
                db, user_id=current_user.id, limit=5
            )
        
        return {
            "status": "success",
            "user": user_info,
            "activities_count": len(activities),
            "activities": [
                {
                    "id": a.id,
                    "type": a.activity_type,
                    "description": a.description,
                    "created_at": a.created_at.isoformat()
                }
                for a in activities[:3]  # Just first 3 for debugging
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "is_parent": current_user.is_parent
            },
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int = Path(..., description="ID of the activity to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityResponse:
    """
    Get a specific activity by ID.
    
    - **Access control**: Users can only access activities they're involved in
    - **Parents**: Can access activities for themselves and their children
    - **Children**: Can only access their own activities
    """
    try:
        activity = await activity_service.get(db, id=activity_id)
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Check access permissions
        if current_user.is_parent:
            # Parents can access activities involving themselves or their children
            from ....models.user import User as UserModel
            children_query = select(UserModel.id).where(UserModel.parent_id == current_user.id)
            children_result = await db.execute(children_query)
            child_ids = children_result.scalars().all()
            family_ids = [current_user.id] + child_ids
            
            if (activity.user_id not in family_ids and 
                (activity.target_user_id is None or activity.target_user_id not in family_ids)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this activity"
                )
        else:
            # Children can only access their own activities
            if activity.user_id != current_user.id and activity.target_user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this activity"
                )
        
        return activity
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity: {str(e)}"
        )