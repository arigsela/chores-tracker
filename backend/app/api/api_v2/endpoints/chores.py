"""Chore management endpoints v2 - JSON-only responses."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated

from ....db.base import get_db
from ....schemas.chore import ChoreCreate, ChoreResponse, ChoreUpdate, ChoreComplete, ChoreApprove, ChoreDisable
from ....schemas.api_response import ApiResponse, PaginatedResponse, SuccessResponse, ErrorResponse
from ....dependencies.auth import get_current_user
from ....dependencies.services import ChoreServiceDep
from ....models.user import User
from ....middleware.rate_limit import limit_api_endpoint_default, limit_update, limit_delete

router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[ChoreResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chore",
    description="""
    Create a new chore assignment.
    
    **Access**: Parents only
    
    **Required fields**:
    - title: Chore name
    - assignee_id: ID of the child who will do the chore
    - reward: Fixed reward amount (or min/max for range rewards)
    """,
    responses={
        201: {"model": ApiResponse[ChoreResponse]},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse}
    }
)
@limit_api_endpoint_default
async def create_chore(
    request: Request,
    chore_data: ChoreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[ChoreResponse]:
    """Create a new chore."""
    if not current_user.is_parent:
        return ApiResponse(
            success=False,
            error="Only parents can create chores",
            data=None
        )
    
    try:
        chore = await chore_service.create_chore(
            db=db,
            creator_id=current_user.id,
            chore_data=chore_data.model_dump()
        )
        
        return ApiResponse(
            success=True,
            data=ChoreResponse.model_validate(chore),
            error=None
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.get(
    "/",
    response_model=PaginatedResponse[ChoreResponse],
    summary="Get chores",
    description="""
    Get chores based on user role.
    
    - **Parents**: See all chores they created
    - **Children**: See chores assigned to them
    
    Supports pagination and filtering.
    """
)
@limit_api_endpoint_default
async def get_chores(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    include_disabled: bool = Query(False, description="Include disabled chores"),
    include_completed: bool = Query(True, description="Include completed chores")
) -> PaginatedResponse[ChoreResponse]:
    """Get paginated list of chores."""
    try:
        chores = await chore_service.get_chores_for_user(db=db, user=current_user)
        
        # Apply filters
        if not include_disabled:
            chores = [c for c in chores if not c.is_disabled]
        if not include_completed:
            chores = [c for c in chores if not c.is_completed]
        
        # Pagination
        total = len(chores)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_chores = chores[start:end]
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            success=True,
            data=[ChoreResponse.model_validate(chore) for chore in paginated_chores],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            error=None
        )
    except Exception as e:
        return PaginatedResponse(
            success=False,
            data=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0,
            error=str(e)
        )


@router.get(
    "/{chore_id}",
    response_model=ApiResponse[ChoreResponse],
    summary="Get chore details",
    description="Get detailed information about a specific chore."
)
async def get_chore(
    chore_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[ChoreResponse]:
    """Get chore details."""
    try:
        chore = await chore_service.get(db=db, id=chore_id)
        if not chore:
            return ApiResponse(
                success=False,
                error="Chore not found",
                data=None
            )
        
        # Check access
        if current_user.is_parent:
            if chore.creator_id != current_user.id:
                return ApiResponse(
                    success=False,
                    error="Not authorized to view this chore",
                    data=None
                )
        else:
            if chore.assignee_id != current_user.id:
                return ApiResponse(
                    success=False,
                    error="Not authorized to view this chore",
                    data=None
                )
        
        return ApiResponse(
            success=True,
            data=ChoreResponse.model_validate(chore),
            error=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.put(
    "/{chore_id}",
    response_model=ApiResponse[ChoreResponse],
    summary="Update chore",
    description="Update chore details. Only the parent who created it can update."
)
@limit_update
async def update_chore(
    request,  # Required for rate limiting
    chore_id: int,
    chore_update: ChoreUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[ChoreResponse]:
    """Update chore details."""
    if not current_user.is_parent:
        return ApiResponse(
            success=False,
            error="Only parents can update chores",
            data=None
        )
    
    try:
        updated_chore = await chore_service.update_chore(
            db=db,
            chore_id=chore_id,
            parent_id=current_user.id,
            update_data=chore_update.model_dump(exclude_unset=True)
        )
        
        return ApiResponse(
            success=True,
            data=ChoreResponse.model_validate(updated_chore),
            error=None
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.post(
    "/{chore_id}/complete",
    response_model=ApiResponse[ChoreResponse],
    summary="Mark chore as complete",
    description="Mark a chore as completed. Only the assigned child can complete."
)
async def complete_chore(
    chore_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[ChoreResponse]:
    """Mark chore as complete."""
    if current_user.is_parent:
        return ApiResponse(
            success=False,
            error="Parents cannot mark chores as complete",
            data=None
        )
    
    try:
        completed_chore = await chore_service.complete_chore(
            db=db,
            chore_id=chore_id,
            child_id=current_user.id
        )
        
        return ApiResponse(
            success=True,
            data=ChoreResponse.model_validate(completed_chore),
            error=None
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.post(
    "/{chore_id}/approve",
    response_model=ApiResponse[ChoreResponse],
    summary="Approve completed chore",
    description="Approve a completed chore and assign reward. Parent only."
)
async def approve_chore(
    chore_id: int,
    approval_data: ChoreApprove,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[ChoreResponse]:
    """Approve completed chore."""
    if not current_user.is_parent:
        return ApiResponse(
            success=False,
            error="Only parents can approve chores",
            data=None
        )
    
    try:
        approved_chore = await chore_service.approve_chore(
            db=db,
            chore_id=chore_id,
            parent_id=current_user.id,
            reward_value=approval_data.reward_value
        )
        
        return ApiResponse(
            success=True,
            data=ChoreResponse.model_validate(approved_chore),
            error=None
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.post(
    "/{chore_id}/disable",
    response_model=SuccessResponse,
    summary="Disable chore",
    description="Soft delete a chore. Parent only."
)
@limit_delete
async def disable_chore(
    request,  # Required for rate limiting
    chore_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> SuccessResponse:
    """Disable a chore."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can disable chores"
        )
    
    try:
        await chore_service.disable_chore(
            db=db,
            chore_id=chore_id,
            parent_id=current_user.id
        )
        
        return SuccessResponse(
            success=True,
            message="Chore disabled successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/stats/summary",
    response_model=ApiResponse[dict],
    summary="Get chore statistics",
    description="Get summary statistics for chores."
)
async def get_chore_stats(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    chore_service: ChoreServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[dict]:
    """Get chore statistics."""
    try:
        if current_user.is_parent:
            # Parent stats: all their created chores
            chores = await chore_service.get_chores_for_user(db=db, user=current_user)
        else:
            # Child stats: their assigned chores
            chores = await chore_service.get_available_chores(db=db, child_id=current_user.id)
        
        # Calculate stats
        total_chores = len(chores)
        completed_chores = len([c for c in chores if c.is_completed])
        approved_chores = len([c for c in chores if c.is_approved])
        pending_approval = len([c for c in chores if c.is_completed and not c.is_approved])
        
        # Calculate earnings
        total_earned = sum(c.reward for c in chores if c.is_approved)
        potential_earnings = sum(c.reward for c in chores if not c.is_approved and not c.is_disabled)
        
        stats = {
            "total_chores": total_chores,
            "completed_chores": completed_chores,
            "approved_chores": approved_chores,
            "pending_approval": pending_approval,
            "total_earned": total_earned,
            "potential_earnings": potential_earnings,
            "completion_rate": (completed_chores / total_chores * 100) if total_chores > 0 else 0
        }
        
        return ApiResponse(
            success=True,
            data=stats,
            error=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )