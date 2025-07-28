"""User management endpoints v2 - JSON-only responses."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated

from ....db.base import get_db
from ....schemas.user import UserCreate, UserResponse, UserUpdate
from ....schemas.api_response import ApiResponse, PaginatedResponse, SuccessResponse, ErrorResponse
from ....dependencies.auth import get_current_user
from ....dependencies.services import UserServiceDep
from ....models.user import User
from ....middleware.rate_limit import limit_register, limit_api_endpoint_default

router = APIRouter()


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new parent or child user account.
    
    **Parent accounts** require:
    - Valid email address
    - Unique username
    - Strong password
    
    **Child accounts** require:
    - Unique username  
    - Password
    - Parent ID (or authenticated as parent)
    
    Rate limited to 3 requests per minute.
    """,
    responses={
        201: {"model": ApiResponse[UserResponse]},
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse}
    }
)
@limit_register
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserServiceDep,
    current_user: Annotated[User, Depends(get_current_user)] = None
) -> ApiResponse[UserResponse]:
    """Register a new user account."""
    try:
        # For child accounts, use current user as parent if not specified
        if not user_data.is_parent and not user_data.parent_id and current_user:
            if current_user.is_parent:
                user_data.parent_id = current_user.id
            else:
                return ApiResponse(
                    success=False,
                    error="Only parents can create child accounts",
                    data=None
                )
        
        user = await user_service.register_user(
            db=db,
            username=user_data.username,
            password=user_data.password,
            is_parent=user_data.is_parent,
            parent_id=user_data.parent_id,
            email=user_data.email
        )
        
        return ApiResponse(
            success=True,
            data=UserResponse.model_validate(user),
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
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current user",
    description="Get the currently authenticated user's information."
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[UserResponse]:
    """Get current user information."""
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        error=None
    )


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    summary="Get all users",
    description="""
    Retrieve a paginated list of users.
    
    **Access**: Admin only (future implementation)
    Currently returns all users for authenticated users.
    """
)
@limit_api_endpoint_default
async def get_users(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserServiceDep,
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
) -> PaginatedResponse[UserResponse]:
    """Get paginated list of users."""
    try:
        offset = (page - 1) * page_size
        users = await user_service.get_multi(db, skip=offset, limit=page_size)
        total = await user_service.count(db)
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            success=True,
            data=[UserResponse.model_validate(user) for user in users],
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
    "/children",
    response_model=ApiResponse[List[UserResponse]],
    summary="Get children for current parent",
    description="Get all child accounts associated with the current parent user."
)
async def get_children(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[List[UserResponse]]:
    """Get children for current parent."""
    if not current_user.is_parent:
        return ApiResponse(
            success=False,
            error="Only parents can view children",
            data=None
        )
    
    try:
        children = await user_service.get_children_for_parent(
            db=db,
            parent_id=current_user.id
        )
        
        return ApiResponse(
            success=True,
            data=[UserResponse.model_validate(child) for child in children],
            error=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Update user",
    description="Update user information. Users can update their own info, parents can update their children."
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ApiResponse[UserResponse]:
    """Update user information."""
    # Check permissions
    if user_id != current_user.id:
        # Check if updating child
        target_user = await user_service.get(db, id=user_id)
        if not target_user or target_user.parent_id != current_user.id:
            return ApiResponse(
                success=False,
                error="Not authorized to update this user",
                data=None
            )
    
    try:
        updated_user = await user_service.update(
            db=db,
            id=user_id,
            obj_in=user_update
        )
        
        return ApiResponse(
            success=True,
            data=UserResponse.model_validate(updated_user),
            error=None
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e),
            data=None
        )


@router.post(
    "/{user_id}/reset-password",
    response_model=SuccessResponse,
    summary="Reset user password",
    description="Reset password for a user. Parents can reset their children's passwords."
)
async def reset_password(
    user_id: int,
    new_password: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserServiceDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> SuccessResponse:
    """Reset user password."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can reset passwords"
        )
    
    try:
        await user_service.reset_child_password(
            db=db,
            parent_id=current_user.id,
            child_id=user_id,
            new_password=new_password
        )
        
        return SuccessResponse(
            success=True,
            message="Password reset successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )