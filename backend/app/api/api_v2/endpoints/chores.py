"""
Enhanced chore endpoints for V2 API with pool management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....dependencies.auth import get_current_user
from ....db.base import get_db
from ....models.user import User
from ....services.chore_service_v2 import ChoreServiceV2
from ....schemas.chore import (
    ChoreCreate,
    ChoreResponse,
    ChoreUpdate,
    ChoreWithAvailability,
    ChoreListResponse
)

router = APIRouter()

chore_service_v2 = ChoreServiceV2()


@router.get(
    "/pool",
    response_model=ChoreListResponse,
    summary="Get master pool chores",
    description="Get all unassigned chores from the master pool with visibility filtering and availability status.",
    responses={
        200: {
            "description": "Pool chores retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "available_chores": [
                            {
                                "id": 1,
                                "title": "Clean Kitchen",
                                "is_available": True,
                                "availability_progress": 100
                            }
                        ],
                        "completed_chores": [
                            {
                                "id": 2,
                                "title": "Take Out Trash",
                                "is_available": False,
                                "availability_progress": 25,
                                "next_available_time": "2024-12-21T00:00:00"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_pool_chores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreListResponse:
    """
    Get master pool chores with visibility and availability.
    
    For children:
    - Shows only unassigned chores not hidden from them
    - Separates available and completed (in cooldown) chores
    - Includes availability progress for recurring chores
    
    For parents:
    - Shows all pool chores they created
    - No visibility filtering applied
    """
    return await chore_service_v2.get_pool_chores(db, user=current_user)


@router.post(
    "/",
    response_model=ChoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chore with visibility settings",
    description="Create a new chore with optional visibility settings. Only parents can create chores."
)
async def create_chore(
    chore: ChoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreResponse:
    """
    Create a new chore with visibility settings.
    
    - **assignee_id**: Optional - leave null for pool chores
    - **hidden_from_users**: List of user IDs to hide the chore from
    - **recurrence_type**: Type of recurrence (none, daily, weekly, monthly)
    - **recurrence_value**: Day of week (0-6) or day of month (1-31)
    """
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can create chores"
        )
    
    # Extract hidden_from_users if present
    chore_data = chore.model_dump()
    hidden_from_users = chore_data.pop("hidden_from_users", [])
    
    # Create chore with visibility
    created_chore = await chore_service_v2.create_chore_with_visibility(
        db,
        creator_id=current_user.id,
        chore_data=chore_data,
        hidden_from_users=hidden_from_users
    )
    
    return ChoreResponse.model_validate(created_chore)


@router.post(
    "/{chore_id}/claim",
    response_model=ChoreResponse,
    summary="Claim an unassigned chore",
    description="Claim an unassigned chore from the pool. Only children can claim chores.",
    responses={
        400: {"description": "Chore already assigned or not available"},
        403: {"description": "Cannot claim this chore"},
        404: {"description": "Chore not found"}
    }
)
async def claim_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreResponse:
    """
    Claim an unassigned chore from the pool.
    
    First-come-first-served: once claimed, other children cannot claim it.
    """
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parents cannot claim chores"
        )
    
    claimed_chore = await chore_service_v2.claim_chore(
        db,
        chore_id=chore_id,
        user_id=current_user.id
    )
    
    return ChoreResponse.model_validate(claimed_chore)


@router.post(
    "/{chore_id}/complete",
    response_model=ChoreResponse,
    summary="Complete a chore",
    description="Mark a chore as complete. If unassigned, will auto-claim first.",
    responses={
        400: {"description": "Cannot complete chore"},
        403: {"description": "Not authorized to complete this chore"},
        404: {"description": "Chore not found"}
    }
)
async def complete_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreResponse:
    """
    Complete a chore with enhanced V2 features.
    
    - Auto-claims if unassigned pool chore
    - Updates recurrence tracking
    - Calculates next available time
    """
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parents cannot complete chores"
        )
    
    completed_chore = await chore_service_v2.complete_chore(
        db,
        chore_id=chore_id,
        user_id=current_user.id
    )
    
    return ChoreResponse.model_validate(completed_chore)


@router.get(
    "/{chore_id}",
    response_model=ChoreWithAvailability,
    summary="Get chore with availability info",
    description="Get a single chore with availability and visibility information.",
    responses={
        404: {"description": "Chore not found"}
    }
)
async def get_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreWithAvailability:
    """
    Get detailed chore information including availability.
    
    Includes:
    - Availability status and progress
    - Whether it's hidden from the current user
    - Next available time for recurring chores
    """
    return await chore_service_v2.get_chore_with_availability(
        db,
        chore_id=chore_id,
        user_id=current_user.id
    )


@router.get(
    "/",
    response_model=List[ChoreResponse],
    summary="Get user's chores",
    description="Get chores based on user role - parents see created chores, children see assigned chores."
)
async def get_chores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_disabled: bool = Query(False, description="Include disabled chores")
) -> List[ChoreResponse]:
    """
    Get chores for the current user.
    
    - Parents: See all chores they created
    - Children: See chores assigned to them (not pool chores)
    """
    chores = await chore_service_v2.get_chores_for_user(db, user=current_user)
    
    # Filter out disabled unless requested
    if not include_disabled:
        chores = [c for c in chores if not c.is_disabled]
    
    return [ChoreResponse.model_validate(chore) for chore in chores]


@router.put(
    "/{chore_id}",
    response_model=ChoreResponse,
    summary="Update a chore",
    description="Update chore details. Only the parent who created it can update."
)
async def update_chore(
    chore_id: int,
    chore_update: ChoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreResponse:
    """
    Update a chore's details.
    
    Cannot update completed or approved chores.
    """
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can update chores"
        )
    
    update_data = chore_update.model_dump(exclude_unset=True)
    
    updated_chore = await chore_service_v2.update_chore(
        db,
        chore_id=chore_id,
        parent_id=current_user.id,
        update_data=update_data
    )
    
    return ChoreResponse.model_validate(updated_chore)