"""
Visibility management endpoints for V2 API.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....dependencies.auth import get_current_user
from ....db.base import get_db
from ....models.user import User
from ....services.chore_visibility_service import ChoreVisibilityService
from ....services.chore_service import ChoreService
from ....schemas.chore_visibility import (
    ChoreVisibilityBulkUpdate,
    ChoreVisibilityResponse,
    ChoreVisibilityUpdate
)

router = APIRouter()

chore_visibility_service = ChoreVisibilityService()
chore_service = ChoreService()


@router.put(
    "/{chore_id}/visibility",
    response_model=List[ChoreVisibilityResponse],
    summary="Update chore visibility settings",
    description="Update which users can see a specific chore. Only parents can manage visibility.",
    responses={
        403: {"description": "Only parents can manage visibility"},
        404: {"description": "Chore not found"}
    }
)
async def update_chore_visibility(
    chore_id: int,
    visibility_update: ChoreVisibilityBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ChoreVisibilityResponse]:
    """
    Update visibility settings for a chore.
    
    - **chore_id**: ID of the chore to update visibility for
    - **hidden_from_users**: List of user IDs to hide the chore from
    - **visible_to_users**: List of user IDs to show the chore to
    
    Only parents can manage chore visibility.
    """
    # Verify chore exists and user is the creator
    chore = await chore_service.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can manage chore visibility"
        )
    
    if chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage visibility for chores you created"
        )
    
    # Ensure we're updating visibility for the correct chore
    visibility_update.chore_id = chore_id
    
    # Update visibility settings
    try:
        updated_records = await chore_visibility_service.bulk_update_visibility(
            db,
            bulk_update=visibility_update,
            current_user=current_user
        )
        
        return [
            ChoreVisibilityResponse(
                id=record.id,
                chore_id=record.chore_id,
                user_id=record.user_id,
                is_hidden=record.is_hidden,
                created_at=record.created_at,
                updated_at=record.updated_at
            )
            for record in updated_records
        ]
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get(
    "/{chore_id}/visibility",
    response_model=List[ChoreVisibilityResponse],
    summary="Get chore visibility settings",
    description="Get current visibility settings for a chore. Only the parent who created the chore can view these settings.",
    responses={
        403: {"description": "Only the chore creator can view visibility settings"},
        404: {"description": "Chore not found"}
    }
)
async def get_chore_visibility(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ChoreVisibilityResponse]:
    """
    Get visibility settings for a chore.
    
    Returns a list of all visibility settings showing which users
    have the chore hidden from them.
    """
    # Verify chore exists and user is the creator
    chore = await chore_service.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view chore visibility settings"
        )
    
    if chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view visibility for chores you created"
        )
    
    # Get visibility settings
    visibility_settings = await chore_visibility_service.get_chore_visibility_settings(
        db, chore_id=chore_id
    )
    
    return [
        ChoreVisibilityResponse(
            id=setting.id,
            chore_id=setting.chore_id,
            user_id=setting.user_id,
            is_hidden=setting.is_hidden,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )
        for setting in visibility_settings
    ]


@router.put(
    "/{chore_id}/visibility/user/{user_id}",
    response_model=ChoreVisibilityResponse,
    summary="Update visibility for a specific user",
    description="Update whether a specific user can see a chore. Only parents can manage visibility.",
    responses={
        403: {"description": "Only parents can manage visibility"},
        404: {"description": "Chore or user not found"}
    }
)
async def update_chore_visibility_for_user(
    chore_id: int,
    user_id: int,
    visibility_update: ChoreVisibilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChoreVisibilityResponse:
    """
    Update visibility of a chore for a specific user.
    
    - **chore_id**: ID of the chore
    - **user_id**: ID of the user to update visibility for
    - **is_hidden**: Whether to hide the chore from this user
    """
    # Verify chore exists and user is the creator
    chore = await chore_service.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can manage chore visibility"
        )
    
    if chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage visibility for chores you created"
        )
    
    # Update visibility
    try:
        visibility_record = await chore_visibility_service.update_chore_visibility(
            db,
            chore_id=chore_id,
            user_id=user_id,
            is_hidden=visibility_update.is_hidden,
            current_user=current_user
        )
        
        return ChoreVisibilityResponse(
            id=visibility_record.id,
            chore_id=visibility_record.chore_id,
            user_id=visibility_record.user_id,
            is_hidden=visibility_record.is_hidden,
            created_at=visibility_record.created_at,
            updated_at=visibility_record.updated_at
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )