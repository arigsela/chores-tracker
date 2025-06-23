from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ....db.base import get_db
from ....schemas.chore import ChoreCreate, ChoreResponse, ChoreUpdate, ChoreApprove, ChoreDisable
from ....dependencies.auth import get_current_user
from ....dependencies.services import ChoreServiceDep
from ....models.user import User
from ....middleware.rate_limit import limit_api_endpoint, limit_create, limit_update, limit_delete

router = APIRouter()

@router.post("/", response_model=ChoreResponse, status_code=status.HTTP_201_CREATED)
@limit_create
async def create_chore(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    reward: Optional[str] = Form(None),
    min_reward: Optional[str] = Form(None),
    max_reward: Optional[str] = Form(None),
    is_range_reward: Optional[str] = Form(None),
    cooldown_days: Optional[int] = Form(None),
    assignee_id: Optional[int] = Form(None),
    is_recurring: Optional[str] = Form(None),
    frequency: Optional[str] = Form(None),
):
    """Create a new chore. Accepts both form data and JSON."""
    # Only parents can create chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can create chores"
        )
    
    chore_data = None
    
    # Check if we're using form data
    if title is not None:  # Form data was provided
        # Convert string form values to appropriate types
        is_recurring_bool = is_recurring == "on"
        is_range_reward_bool = is_range_reward == "on"
        
        chore_data = {
            "title": title,
            "description": description or "",
            "is_range_reward": is_range_reward_bool,
            "assignee_id": int(assignee_id) if assignee_id is not None else None,
            "is_recurring": is_recurring_bool,
            "frequency": frequency if is_recurring_bool else None,
            "cooldown_days": int(cooldown_days) if cooldown_days is not None else 0,
        }
        
        # Set reward fields based on whether it's a range or fixed
        if is_range_reward_bool:
            chore_data["min_reward"] = float(min_reward) if min_reward and min_reward.strip() else 0.0
            chore_data["max_reward"] = float(max_reward) if max_reward and max_reward.strip() else 0.0
            # For range rewards, we don't need the 'reward' field
            chore_data["reward"] = 0.0  # Default value
        else:
            # For fixed rewards, we need the 'reward' field
            chore_data["reward"] = float(reward) if reward and reward.strip() else 0.0
    else:
        # Must be JSON data, try to parse it
        try:
            json_body = await request.json()
            chore_data = json_body
        except:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON data or missing required fields"
            )
    
    # Validate required fields in JSON data
    if not chore_data or "title" not in chore_data or "assignee_id" not in chore_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required fields: title and assignee_id"
        )
    
    # Use service to create chore
    try:
        chore = await chore_service.create_chore(
            db=db,
            creator_id=current_user.id,
            chore_data=chore_data
        )
        return chore
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[ChoreResponse])
async def read_chores(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Get chores based on user role."""
    chores = await chore_service.get_chores_for_user(db, user=current_user)
    return chores

@router.get("/available", response_model=List[ChoreResponse])
async def read_available_chores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Get available chores for a child (not completed or past cooldown)."""
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for children users"
        )
    
    chores = await chore_service.get_available_chores(db, child_id=current_user.id)
    return chores

@router.get("/pending-approval", response_model=List[ChoreResponse])
async def read_pending_approval(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Get chores pending approval for a parent."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for parent users"
        )
    
    chores = await chore_service.get_pending_approval(db, parent_id=current_user.id)
    return chores

@router.get("/child/{child_id}", response_model=List[ChoreResponse])
async def read_child_chores(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Get all chores for a specific child (parent view)."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view children's chores"
        )
    
    chores = await chore_service.get_child_chores(
        db,
        parent_id=current_user.id,
        child_id=child_id
    )
    return chores

@router.get("/child/{child_id}/completed", response_model=List[ChoreResponse])
async def read_child_completed_chores(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Get completed chores for a specific child (parent view)."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view children's completed chores"
        )
    
    # Verify child belongs to parent (service will handle)
    await chore_service.get_child_chores(
        db,
        parent_id=current_user.id,
        child_id=child_id
    )
    
    # Get completed chores
    chores = await chore_service.repository.get_completed_by_child(db, child_id=child_id)
    return chores

@router.get("/{chore_id}", response_model=ChoreResponse)
async def read_chore(
    chore_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Get a specific chore."""
    chore = await chore_service.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    # Check permissions
    if current_user.is_parent and chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chore"
        )
    
    if not current_user.is_parent and chore.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this chore"
        )
    
    return chore

@router.put("/{chore_id}", response_model=ChoreResponse)
async def update_chore(
    chore_id: int,
    chore_in: ChoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Update a chore."""
    # Only parents can update chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can update chores"
        )
    
    updated_chore = await chore_service.update_chore(
        db,
        chore_id=chore_id,
        parent_id=current_user.id,
        update_data=chore_in.model_dump(exclude_unset=True)
    )
    return updated_chore

@router.delete("/{chore_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Delete a chore."""
    # Only parents can delete chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can delete chores"
        )
    
    # Service will verify ownership and delete the chore
    await chore_service.delete_chore(
        db,
        chore_id=chore_id,
        parent_id=current_user.id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{chore_id}/complete", response_model=ChoreResponse)
async def complete_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Mark a chore as completed."""
    # Only children can complete chores
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parents cannot complete chores"
        )
    
    # Service will handle all business logic including cooldown checks
    updated_chore = await chore_service.complete_chore(
        db,
        chore_id=chore_id,
        user_id=current_user.id
    )
    return updated_chore

@router.post("/{chore_id}/approve", response_model=ChoreResponse)
async def approve_chore(
    chore_id: int,
    approval_data: ChoreApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Approve a completed chore with optional reward value for range-based rewards."""
    # Only parents can approve chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can approve chores"
        )
    
    # Service will handle all business logic
    updated_chore = await chore_service.approve_chore(
        db,
        chore_id=chore_id,
        parent_id=current_user.id,
        reward_value=approval_data.reward_value
    )
    return updated_chore

@router.post("/{chore_id}/disable", response_model=ChoreResponse)
async def disable_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """Disable a chore."""
    # Only parents can disable chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can disable chores"
        )
    
    # Service will handle authorization and disable
    updated_chore = await chore_service.disable_chore(
        db,
        chore_id=chore_id,
        parent_id=current_user.id
    )
    return updated_chore