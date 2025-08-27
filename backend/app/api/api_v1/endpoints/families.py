"""Family management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ....db.base import get_db
from ....schemas.family import (
    FamilyCreate, FamilyResponse, FamilyJoinRequest, FamilyJoinResponse,
    InviteCodeGenerateRequest, InviteCodeResponse, FamilyMembersResponse,
    FamilyStatsResponse, FamilyContextResponse, RemoveUserFromFamilyRequest,
    RemoveUserFromFamilyResponse, FamilyMemberResponse, FamilyInviteCodeCleanupResponse
)
from ....dependencies.auth import (
    get_current_user, get_current_parent, get_current_user_with_family,
    require_family_membership, UserWithFamily
)
from ....services.family import FamilyService
from ....services.user_service import UserService
from ....models.user import User
from ....core.exceptions import ValidationError, NotFoundError, AuthorizationError

router = APIRouter()


@router.post("/create", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    family_data: FamilyCreate,
    current_user: User = Depends(get_current_parent),
    family_service: FamilyService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new family for the current parent user.
    
    **Requirements:**
    - User must be a parent
    - User must not already be in a family
    
    **Returns:**
    - Family details including unique invite code
    """
    try:
        family = await family_service.create_family_for_user(
            db, user_id=current_user.id, family_name=family_data.name
        )
        return family
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/join", response_model=FamilyJoinResponse)
async def join_family(
    join_request: FamilyJoinRequest,
    current_user: User = Depends(get_current_parent),
    family_service: FamilyService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Join an existing family using an invite code.
    
    **Requirements:**
    - User must be a parent
    - User must not already be in a family
    - Invite code must be valid and not expired
    
    **Returns:**
    - Success confirmation with family details
    """
    try:
        family = await family_service.join_family_by_code(
            db, user_id=current_user.id, invite_code=join_request.invite_code
        )
        return FamilyJoinResponse(
            success=True,
            family_id=family.id,
            family_name=family.name,
            message="Successfully joined family"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/invite-code/generate", response_model=InviteCodeResponse)
async def generate_invite_code(
    request: InviteCodeGenerateRequest,
    user_with_family: UserWithFamily = Depends(require_family_membership),
    family_service: FamilyService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new invite code for the current user's family.
    
    **Requirements:**
    - User must be a parent
    - User must be in a family
    
    **Returns:**
    - New invite code with expiration details
    """
    if not user_with_family.user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can generate invite codes"
        )
    
    try:
        new_code = await family_service.generate_new_invite_code(
            db,
            family_id=user_with_family.family.id,
            requesting_user_id=user_with_family.user.id,
            expires_in_days=request.expires_in_days
        )
        
        # Calculate expiration time if provided
        expires_at = None
        if request.expires_in_days:
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        return InviteCodeResponse(
            invite_code=new_code,
            expires_at=expires_at,
            family_name=user_with_family.family.name
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/members", response_model=FamilyMembersResponse)
async def get_family_members(
    user_with_family: UserWithFamily = Depends(require_family_membership),
    family_service: FamilyService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all members of the current user's family.
    
    **Requirements:**
    - User must be in a family
    
    **Returns:**
    - Organized list of family members (parents and children)
    """
    try:
        all_members = await family_service.get_family_members(
            db,
            family_id=user_with_family.family.id,
            requesting_user_id=user_with_family.user.id
        )
        parents = await family_service.get_family_parents(
            db,
            family_id=user_with_family.family.id,
            requesting_user_id=user_with_family.user.id
        )
        children = await family_service.get_family_children(
            db,
            family_id=user_with_family.family.id,
            requesting_user_id=user_with_family.user.id
        )
        
        return FamilyMembersResponse(
            family_id=user_with_family.family.id,
            family_name=user_with_family.family.name,
            total_members=len(all_members),
            parents=[FamilyMemberResponse.model_validate(parent) for parent in parents],
            children=[FamilyMemberResponse.model_validate(child) for child in children]
        )
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/stats", response_model=FamilyStatsResponse)
async def get_family_stats(
    user_with_family: UserWithFamily = Depends(require_family_membership),
    family_service: FamilyService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive statistics for the current user's family.
    
    **Requirements:**
    - User must be in a family
    
    **Returns:**
    - Family statistics including member counts, chore activity, and rewards
    """
    try:
        stats = await family_service.get_family_stats(
            db,
            family_id=user_with_family.family.id,
            requesting_user_id=user_with_family.user.id
        )
        return FamilyStatsResponse(**stats)
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/context", response_model=FamilyContextResponse)
async def get_family_context(
    user_with_family: UserWithFamily = Depends(get_current_user_with_family),
    user_service: UserService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's family context and capabilities.
    
    **Returns:**
    - Family information and user's permissions within the family
    """
    return FamilyContextResponse(
        has_family=user_with_family.family is not None,
        family=FamilyResponse.model_validate(user_with_family.family) if user_with_family.family else None,
        role=user_with_family.family_role,
        can_invite=user_with_family.user.is_parent and user_with_family.family is not None,
        can_manage=user_with_family.user.is_parent and user_with_family.family is not None
    )


@router.delete("/members/{user_id}", response_model=RemoveUserFromFamilyResponse)
async def remove_family_member(
    user_id: int,
    request: RemoveUserFromFamilyRequest,
    user_with_family: UserWithFamily = Depends(require_family_membership),
    family_service: FamilyService = Depends(),
    user_service: UserService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a user from the current family.
    
    **Requirements:**
    - Current user must be a parent
    - Current user must be in a family
    - Cannot remove the last parent from a family
    
    **Returns:**
    - Confirmation of user removal
    """
    if not user_with_family.user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can remove family members"
        )
    
    # Ensure user_id matches the path parameter
    if request.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path must match user ID in request body"
        )
    
    try:
        await family_service.remove_user_from_family(
            db,
            user_id=user_id,
            family_id=user_with_family.family.id,
            requesting_user_id=user_with_family.user.id
        )
        
        return RemoveUserFromFamilyResponse(
            success=True,
            message=f"User {user_id} successfully removed from family",
            removed_user_id=user_id
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/admin/cleanup-invite-codes", response_model=FamilyInviteCodeCleanupResponse)
async def cleanup_expired_invite_codes(
    current_user: User = Depends(get_current_parent),
    family_service: FamilyService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Administrative endpoint to clean up expired invite codes.
    
    This is a maintenance operation that regenerates new codes for families
    with expired invite codes.
    
    **Requirements:**
    - User must be a parent (basic authorization for now)
    
    **Returns:**
    - Count of cleaned up invite codes
    
    **Note:** In production, this should be restricted to admin users or run as a background job.
    """
    try:
        cleaned_count = await family_service.cleanup_expired_invite_codes(db)
        
        return FamilyInviteCodeCleanupResponse(
            cleaned_count=cleaned_count,
            message=f"Successfully regenerated {cleaned_count} expired invite codes"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}"
        )