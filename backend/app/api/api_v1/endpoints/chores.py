from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, Body, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ....db.base import get_db
from ....schemas.chore import ChoreCreate, ChoreResponse, ChoreUpdate, ChoreApprove, ChoreDisable, ChoreReject
from ....dependencies.auth import get_current_user
from ....dependencies.services import ChoreServiceDep
from ....models.user import User
from ....middleware.rate_limit import limit_api_endpoint, limit_create, limit_update, limit_delete

router = APIRouter()

@router.post(
    "",
    response_model=ChoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chore",
    description="""
    Create a new chore and assign it to a child.
    
    **Access**: Parents only
    
    **Reward Types**:
    - **Fixed reward**: Set a single reward amount
    - **Range reward**: Set min/max reward amounts (parent chooses exact amount during approval)
    
    **Recurrence**:
    - Set `is_recurring=true` and `cooldown_days` for recurring chores
    - Cooldown prevents immediate re-completion (e.g., 1 for daily, 7 for weekly)
    
    This endpoint accepts both JSON and form data.
    
    Rate limited to 30 requests per minute.
    """,
    responses={
        201: {
            "description": "Chore created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room",
                        "description": "Clean and organize bedroom",
                        "reward": 5.0,
                        "is_range_reward": False,
                        "min_reward": None,
                        "max_reward": None,
                        "cooldown_days": 7,
                        "is_recurring": True,
                        "assignee_id": 2,
                        "creator_id": 1,
                        "is_completed": False,
                        "is_approved": False,
                        "is_disabled": False,
                        "created_at": "2024-12-24T12:00:00"
                    }
                }
            }
        },
        403: {
            "description": "Only parents can create chores",
            "content": {
                "application/json": {
                    "example": {"detail": "Only parents can create chores"}
                }
            }
        },
        404: {
            "description": "Assignee not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Assignee not found"}
                }
            }
        }
    }
)
@limit_create
async def create_chore(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None,
    title: Optional[str] = Form(None, description="Chore title"),
    description: Optional[str] = Form(None, description="Detailed description"),
    reward: Optional[str] = Form(None, description="Fixed reward amount"),
    min_reward: Optional[str] = Form(None, description="Minimum reward for range"),
    max_reward: Optional[str] = Form(None, description="Maximum reward for range"),
    is_range_reward: Optional[str] = Form(None, description="'on' for range reward"),
    cooldown_days: Optional[int] = Form(None, description="Days before can complete again"),
    assignee_id: Optional[int] = Form(None, description="Child's user ID"),
    is_recurring: Optional[str] = Form(None, description="'on' for recurring chore"),
    frequency: Optional[str] = Form(None, description="Legacy: use cooldown_days instead"),
):
    """
    Create a new chore and assign it to a child.
    
    Parents can create chores with fixed or range-based rewards.
    Recurring chores automatically reset after completion and cooldown.
    """
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
    if not chore_data or "title" not in chore_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing required field: title"
        )

    # Convert legacy assignee_id to assignee_ids for backward compatibility
    if "assignee_id" in chore_data and "assignee_ids" not in chore_data:
        assignee_id = chore_data.pop("assignee_id")
        if assignee_id is not None:
            chore_data["assignee_ids"] = [assignee_id]
            chore_data.setdefault("assignment_mode", "single")
        else:
            chore_data["assignee_ids"] = []
            chore_data.setdefault("assignment_mode", "unassigned")
    
    # Use service to create chore
    try:
        chore = await chore_service.create_chore(
            db=db,
            creator_id=current_user.id,
            chore_data=chore_data
        )

        # Eager-load assignments to avoid lazy-load errors when serializing response
        chore_with_assignments = await chore_service.repository.get_with_assignments(
            db,
            chore_id=chore.id
        )
        return chore_with_assignments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "",
    response_model=List[ChoreResponse],
    summary="Get chores (with optional filters)",
    description="""
    Get chores visible to the current user, with optional filters.
    
    **Access patterns**:
    - **Parents**: Base scope is chores they created; can filter by `child_id`
    - **Children**: Base scope is chores assigned to them
    
    **Optional filters** (applied after base scope):
    - `state`: one of `active`, `completed`, `pending-approval`
    - `child_id`: only for parents, filter to a specific child
    
    Results include active and disabled chores, but not deleted ones.
    """,
    responses={
        200: {
            "description": "List of chores",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Clean Room",
                            "description": "Clean and organize bedroom",
                            "reward": 5.0,
                            "assignee_id": 2,
                            "is_completed": False,
                            "is_approved": False,
                            "is_disabled": False
                        }
                    ]
                }
            }
        }
    }
)
async def read_chores(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    state: Optional[str] = Query(None, description="Filter by state: active|completed|pending-approval"),
    child_id: Optional[int] = Query(None, description="Parent-only: filter chores for a specific child"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Get chores visible to the current user with optional state and child filters.
    """
    # Base scope
    if current_user.is_parent:
        if child_id is not None:
            # Verify child belongs to parent and fetch chores
            chores = await chore_service.get_child_chores(db, parent_id=current_user.id, child_id=child_id)
        else:
            chores = await chore_service.get_chores_for_user(db, user=current_user)
    else:
        chores = await chore_service.get_chores_for_user(db, user=current_user)

    # Apply state filter
    if state:
        if state == "active":
            chores = [c for c in chores if not c.is_completed]
        elif state == "completed":
            chores = [c for c in chores if c.is_completed and c.is_approved]
        elif state == "pending-approval":
            if current_user.is_parent:
                chores = [c for c in chores if c.is_completed and not c.is_approved]
            else:
                chores = [c for c in chores if c.is_completed and not c.is_approved]
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid state. Must be one of: active, completed, pending-approval",
            )

    return chores

@router.get(
    "/available",
    response_model=Dict[str, Any],
    summary="Get available chores for child with multi-assignment support",
    description="""
    Get chores that are currently available for the child to complete.

    **Access**: Children only

    **Returns**:
    - `assigned`: List of chores with existing assignments (not completed, outside cooldown)
    - `pool`: List of unassigned pool chores available to claim
    - `total_count`: Total number of available chores

    **Each chore entry includes**:
    - `chore`: The chore object
    - `assignment`: The assignment object (null for pool chores)
    - `assignment_id`: The assignment ID (null for pool chores)

    **Availability criteria**:
    - Assigned chores: Not completed, not disabled, outside cooldown
    - Pool chores: Unassigned mode, not disabled, not already claimed by child

    This endpoint helps children see what tasks they can work on right now.
    """,
    responses={
        200: {
            "description": "Available chores grouped by type",
            "content": {
                "application/json": {
                    "example": {
                        "assigned": [
                            {
                                "chore": {
                                    "id": 1,
                                    "title": "Clean Your Room",
                                    "description": "Vacuum and organize",
                                    "reward": 5.0,
                                    "assignment_mode": "single"
                                },
                                "assignment": {
                                    "id": 10,
                                    "assignee_id": 2,
                                    "is_completed": False
                                },
                                "assignment_id": 10
                            }
                        ],
                        "pool": [
                            {
                                "chore": {
                                    "id": 3,
                                    "title": "Walk the Dog",
                                    "description": "30 minute walk",
                                    "reward": 3.0,
                                    "assignment_mode": "unassigned"
                                },
                                "assignment": None,
                                "assignment_id": None
                            }
                        ],
                        "total_count": 2
                    }
                }
            }
        },
        403: {
            "description": "Endpoint is only for children",
            "content": {
                "application/json": {
                    "example": {"detail": "This endpoint is only for children users"}
                }
            }
        }
    }
)
async def read_available_chores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Get chores currently available for a child to complete.

    Returns both assigned chores and pool chores with assignment details.
    """
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for children users"
        )

    result = await chore_service.get_available_chores(db, child_id=current_user.id)
    return result

@router.get(
    "/pending-approval",
    response_model=List[Dict[str, Any]],
    summary="Get assignments pending approval with multi-assignment support",
    description="""
    Get all assignments that have been completed by children and are awaiting parent approval.

    **Access**: Parents only

    **Returns assignment-level data**, not chore-level, which is crucial for multi-assignment:
    - For single mode: 1 assignment per chore
    - For multi_independent mode: Multiple assignments (one per child) for the same chore

    **Each result includes**:
    - `assignment`: The ChoreAssignment object
    - `assignment_id`: Assignment ID (use this for approval/rejection)
    - `chore`: The Chore object
    - `assignee`: The User object (child who completed it)
    - `assignee_name`: Child's username for display

    **Family-aware**: Parents see pending assignments from all family chores, not just those they personally created.

    This is the parent's "inbox" for reviewing completed work.
    """,
    responses={
        200: {
            "description": "List of pending assignments with full context",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "assignment": {
                                "id": 15,
                                "chore_id": 3,
                                "assignee_id": 2,
                                "is_completed": True,
                                "is_approved": False,
                                "completion_date": "2024-12-24T14:30:00"
                            },
                            "assignment_id": 15,
                            "chore": {
                                "id": 3,
                                "title": "Wash dishes",
                                "description": "Clean all dirty dishes",
                                "reward": 3.0,
                                "assignment_mode": "single",
                                "is_range_reward": True,
                                "min_reward": 3.0,
                                "max_reward": 5.0
                            },
                            "assignee": {
                                "id": 2,
                                "username": "alice",
                                "is_parent": False
                            },
                            "assignee_name": "alice"
                        }
                    ]
                }
            }
        },
        403: {
            "description": "Endpoint is only for parents",
            "content": {
                "application/json": {
                    "example": {"detail": "This endpoint is only for parent users"}
                }
            }
        }
    }
)
async def read_pending_approval(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Get assignments that have been completed by children and need parent approval.

    Returns assignment-level data with full context (chore + assignee details).
    For range-based rewards, parents will need to specify the exact reward amount during approval.
    """
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for parent users"
        )

    pending_assignments = await chore_service.get_pending_approval(db, parent_id=current_user.id)
    return pending_assignments

@router.get(
    "/child/{child_id}",
    response_model=List[ChoreResponse],
    summary="Get chores for a specific child",
    description="""
    Get all chores assigned to a specific child.
    
    **Access**: Parents only
    
    **Use case**: Parents viewing a child's chore list to see their assignments,
    progress, and completion history.
    
    **Authorization**: Parent must be the child's parent (verified by parent_id relationship).
    """,
    responses={
        200: {
            "description": "List of child's chores",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Make bed",
                            "assignee_id": 2,
                            "is_completed": True,
                            "is_approved": True,
                            "reward": 1.0
                        },
                        {
                            "id": 3,
                            "title": "Homework",
                            "assignee_id": 2,
                            "is_completed": False,
                            "is_recurring": True,
                            "cooldown_days": 1
                        }
                    ]
                }
            }
        },
        403: {
            "description": "Not authorized to view this child's chores"
        },
        404: {
            "description": "Child not found or not your child"
        }
    }
)
async def read_child_chores(
    child_id: int = Path(..., description="The child's user ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Get all chores for a specific child.

    Returns both active and completed chores for the specified child.
    """
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

    # DEBUG: Log what we're about to return
    print(f"[CHILD CHORES API] Returning {len(chores)} chores for child {child_id}")
    for idx, chore in enumerate(chores):
        print(f"[CHILD CHORES API] Chore {idx + 1}: id={chore.id}, title={chore.title}")
        print(f"[CHILD CHORES API]   has is_completed attr: {hasattr(chore, 'is_completed')}")
        print(f"[CHILD CHORES API]   has is_approved attr: {hasattr(chore, 'is_approved')}")
        if hasattr(chore, 'is_completed'):
            print(f"[CHILD CHORES API]   is_completed={chore.is_completed}, is_approved={chore.is_approved}")
            print(f"[CHILD CHORES API]   completed_at={chore.completed_at}, approved_at={chore.approved_at}")

    return chores

@router.get(
    "/child/{child_id}/completed",
    response_model=List[ChoreResponse],
    summary="Get completed chores for a child",
    description="""
    Get all completed chores for a specific child, useful for tracking earnings and history.
    
    **Access**: Parents only
    
    **Returns**: All chores where:
    - Assigned to the specified child
    - Marked as completed (regardless of approval status)
    
    **Use cases**:
    - Calculate total earnings
    - Review completion history
    - Generate allowance reports
    """,
    responses={
        200: {
            "description": "List of completed chores",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Clean room",
                            "is_completed": True,
                            "is_approved": True,
                            "completed_at": "2024-12-20T14:00:00",
                            "approved_at": "2024-12-20T16:00:00",
                            "reward": 5.0
                        },
                        {
                            "id": 3,
                            "title": "Wash dishes",
                            "is_completed": True,
                            "is_approved": False,
                            "completed_at": "2024-12-24T10:00:00",
                            "reward": 3.0
                        }
                    ]
                }
            }
        },
        403: {
            "description": "Not authorized to view this child's chores"
        }
    }
)
async def read_child_completed_chores(
    child_id: int = Path(..., description="The child's user ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Get completed chores for a specific child.
    
    Includes both approved and pending-approval completed chores.
    """
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

@router.get(
    "/{chore_id}",
    response_model=ChoreResponse,
    summary="Get a specific chore",
    description="""
    Retrieve details of a specific chore by ID.
    
    **Access control**:
    - Parents can only view chores they created
    - Children can only view chores assigned to them
    """,
    responses={
        200: {
            "description": "Chore details",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room",
                        "description": "Clean and organize bedroom",
                        "reward": 5.0,
                        "is_range_reward": False,
                        "assignee_id": 2,
                        "creator_id": 1,
                        "is_completed": False,
                        "is_approved": False,
                        "is_recurring": True,
                        "cooldown_days": 7,
                        "created_at": "2024-12-20T10:00:00",
                        "updated_at": "2024-12-20T10:00:00"
                    }
                }
            }
        },
        403: {
            "description": "Not authorized to access this chore"
        },
        404: {
            "description": "Chore not found"
        }
    }
)
async def read_chore(
    chore_id: int = Path(..., description="The ID of the chore to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Get detailed information about a specific chore.
    
    Users can only access chores they're authorized to view.
    """
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

@router.put(
    "/{chore_id}",
    response_model=ChoreResponse,
    summary="Update a chore",
    description="""
    Update an existing chore's details.
    
    **Access**: Parents only (must be the chore creator)
    
    **Updatable fields**:
    - Title and description
    - Reward amount or range
    - Assignee (reassign to different child)
    - Recurrence settings
    
    **Note**: You cannot update a chore that's currently pending approval.
    
    Rate limited to 60 requests per minute.
    """,
    responses={
        200: {
            "description": "Chore updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room (Updated)",
                        "description": "Deep clean and organize bedroom",
                        "reward": 7.0,
                        "updated_at": "2024-12-24T15:00:00"
                    }
                }
            }
        },
        403: {
            "description": "Only parents can update chores"
        },
        404: {
            "description": "Chore not found or not owned by user"
        }
    }
)
@limit_update
async def update_chore(
    request: Request,
    chore_id: int = Path(..., description="The ID of the chore to update"),
    chore_in: ChoreUpdate = Body(..., description="Updated chore data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Update a chore's details.
    
    Only the parent who created the chore can update it.
    """
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

@router.delete(
    "/{chore_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chore",
    description="""
    Permanently delete a chore from the system.
    
    **Access**: Parents only (must be the chore creator)
    
    **Warning**: This action cannot be undone. Consider using the disable endpoint instead
    if you want to temporarily hide a chore.
    
    Rate limited to 20 requests per minute.
    """,
    responses={
        204: {
            "description": "Chore deleted successfully"
        },
        403: {
            "description": "Only parents can delete chores"
        },
        404: {
            "description": "Chore not found or not owned by user"
        }
    }
)
@limit_delete
async def delete_chore(
    request: Request,
    chore_id: int = Path(..., description="The ID of the chore to delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Permanently delete a chore.
    
    This is a hard delete. For soft deletion, use the disable endpoint.
    """
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

@router.post(
    "/{chore_id}/complete",
    response_model=Dict[str, Any],
    summary="Mark chore as completed with multi-assignment support",
    description="""
    Mark a chore as completed and ready for parent approval.

    **Access**: Children only

    **Multi-assignment handling**:
    - **Single mode**: Child must be the assigned child
    - **Multi-independent mode**: Child completes their own assignment independently
    - **Unassigned mode**: Child claims the chore and completes it

    **Business rules**:
    - Child must be assigned (or chore must be unassigned pool)
    - Assignment cannot already be completed (pending approval)
    - For recurring chores: must be outside cooldown period
    - Chore cannot be disabled

    **Returns**:
    - `chore`: The chore object
    - `assignment`: The assignment that was marked complete
    - `message`: Success message

    After completion, the assignment enters "pending approval" state and appears
    in the parent's pending approval list.
    """,
    responses={
        200: {
            "description": "Assignment marked as completed",
            "content": {
                "application/json": {
                    "example": {
                        "chore": {
                            "id": 1,
                            "title": "Clean Room",
                            "assignment_mode": "single"
                        },
                        "assignment": {
                            "id": 10,
                            "chore_id": 1,
                            "assignee_id": 2,
                            "is_completed": True,
                            "is_approved": False,
                            "completion_date": "2024-12-24T16:00:00"
                        },
                        "message": "Chore completed successfully. Awaiting parent approval."
                    }
                }
            }
        },
        403: {
            "description": "Not authorized or parents cannot complete chores"
        },
        400: {
            "description": "Assignment already completed or in cooldown period",
            "content": {
                "application/json": {
                    "example": {"detail": "Assignment is in cooldown period. Can complete again in 5 days."}
                }
            }
        }
    }
)
async def complete_chore(
    chore_id: int = Path(..., description="The ID of the chore to complete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Mark a chore as completed by the child.

    Returns the chore and assignment details. The assignment will need parent approval before rewards are granted.
    """
    # Only children can complete chores
    if current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parents cannot complete chores"
        )

    # Service will handle all business logic including cooldown checks
    result = await chore_service.complete_chore(
        db,
        chore_id=chore_id,
        user_id=current_user.id
    )
    return result

@router.post(
    "/{chore_id}/approve",
    response_model=ChoreResponse,
    summary="Approve a completed chore",
    description="""
    Approve a chore that has been marked as completed by a child.
    
    **Access**: Parents only (must be the chore creator)
    
    **Reward handling**:
    - **Fixed rewards**: Automatically uses the preset reward amount
    - **Range rewards**: Parent must specify reward_value within min/max range
    
    **Workflow**:
    1. Child marks chore as completed
    2. Parent reviews and approves with final reward
    3. For recurring chores: cooldown period begins
    
    Approved chores contribute to the child's total earned rewards.
    """,
    responses={
        200: {
            "description": "Chore approved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room",
                        "is_completed": True,
                        "is_approved": True,
                        "approved_at": "2024-12-24T17:00:00",
                        "reward": 5.0
                    }
                }
            }
        },
        400: {
            "description": "Invalid reward value or chore not completed",
            "content": {
                "application/json": {
                    "example": {"detail": "Reward value must be between 3.0 and 7.0"}
                }
            }
        },
        403: {
            "description": "Only parents can approve chores"
        },
        404: {
            "description": "Chore not found"
        }
    }
)
async def approve_chore(
    chore_id: int = Path(..., description="The ID of the chore to approve"),
    approval_data: ChoreApprove = Body(..., description="Approval data with optional reward value"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Approve a completed chore and set the final reward amount.
    
    For range-based rewards, the reward_value must be within the defined range.
    """
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

@router.post(
    "/{chore_id}/reject",
    response_model=ChoreResponse,
    summary="Reject a completed chore",
    description="""
    Reject a chore that has been marked as completed by a child.
    
    **Access**: Parents only (must be the chore creator)
    
    **Workflow**:
    1. Child marks chore as completed
    2. Parent reviews and rejects with reason
    3. Chore status reverts to incomplete
    4. Child can see rejection reason and redo the chore
    
    **Rejection behavior**:
    - Chore is_completed becomes False
    - completion_date is reset to None
    - rejection_reason is stored for child to view
    """,
    responses={
        200: {
            "description": "Chore rejected successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room",
                        "is_completed": False,
                        "is_approved": False,
                        "completion_date": None,
                        "rejection_reason": "Please clean more thoroughly and organize items properly"
                    }
                }
            }
        },
        400: {
            "description": "Chore not completed or already approved",
            "content": {
                "application/json": {
                    "example": {"detail": "Chore must be completed before rejection"}
                }
            }
        },
        403: {
            "description": "Only parents can reject chores"
        },
        404: {
            "description": "Chore not found"
        },
        422: {
            "description": "Rejection reason is required"
        }
    }
)
async def reject_chore(
    chore_id: int = Path(..., description="The ID of the chore to reject"),
    rejection_data: ChoreReject = Body(..., description="Rejection data with reason"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Reject a completed chore with a reason.
    
    The chore will be reset to incomplete status and the child can redo it.
    """
    # Only parents can reject chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can reject chores"
        )
    
    # Service will handle all business logic
    updated_chore = await chore_service.reject_chore(
        db,
        chore_id=chore_id,
        parent_id=current_user.id,
        rejection_reason=rejection_data.rejection_reason
    )
    return updated_chore

@router.post(
    "/{chore_id}/disable",
    response_model=ChoreResponse,
    summary="Disable a chore",
    description="""
    Soft delete a chore by marking it as disabled.
    
    **Access**: Parents only (must be the chore creator)
    
    **Effects**:
    - Chore no longer appears in active lists
    - Children cannot complete disabled chores
    - Preserves historical data and completion records
    - Can be re-enabled later if needed
    
    This is preferred over deletion when you want to temporarily remove a chore
    or preserve completion history.
    """,
    responses={
        200: {
            "description": "Chore disabled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room",
                        "is_disabled": True,
                        "updated_at": "2024-12-24T18:00:00"
                    }
                }
            }
        },
        403: {
            "description": "Only parents can disable chores"
        },
        404: {
            "description": "Chore not found or not owned by user"
        }
    }
)
async def disable_chore(
    chore_id: int = Path(..., description="The ID of the chore to disable"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Disable a chore (soft delete).
    
    The chore will be hidden from active lists but data is preserved.
    """
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


@router.post(
    "/{chore_id}/enable",
    response_model=ChoreResponse,
    summary="Enable a disabled chore",
    description="""
    Enable a previously disabled chore, making it active again.
    
    **Access**: Parents only (must be the chore creator)
    
    **Effects**:
    - Chore reappears in active lists
    - Children can complete the chore again
    - Retains all previous completion history
    
    This endpoint is used to reactivate a temporarily disabled chore.
    """,
    responses={
        200: {
            "description": "Chore enabled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Clean Room",
                        "is_disabled": False,
                        "updated_at": "2024-12-24T18:00:00"
                    }
                }
            }
        },
        400: {
            "description": "Chore is not disabled"
        },
        403: {
            "description": "Only parents can enable chores"
        },
        404: {
            "description": "Chore not found or not owned by user"
        }
    }
)
async def enable_chore(
    chore_id: int = Path(..., description="The ID of the chore to enable"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    chore_service: ChoreServiceDep = None
):
    """
    Enable a disabled chore.
    
    The chore will be visible in active lists and can be completed again.
    """
    # Only parents can enable chores
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can enable chores"
        )
    
    # Get the chore using the repository
    from ....repositories.chore import ChoreRepository
    chore_repo = ChoreRepository()
    
    chore = await chore_repo.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    # Check if the parent owns this chore
    if chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only enable chores you created"
        )
    
    # Check if the chore is actually disabled
    if not chore.is_disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chore is not disabled"
        )
    
    # Enable the chore using the repository
    updated_chore = await chore_repo.enable_chore(db, chore_id=chore_id)
    
    return updated_chore