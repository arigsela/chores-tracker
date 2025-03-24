from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from ....db.base import get_db
from ....repositories.chore import ChoreRepository
from ....repositories.user import UserRepository
from ....schemas.chore import ChoreCreate, ChoreResponse, ChoreUpdate
from ....dependencies.auth import get_current_user
from ....models.user import User

router = APIRouter()
chore_repo = ChoreRepository()
user_repo = UserRepository()

@router.post("/", response_model=ChoreResponse, status_code=status.HTTP_201_CREATED)
async def create_chore(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    reward: Optional[float] = Form(None),
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
        # Convert is_recurring from string to boolean
        is_recurring_bool = is_recurring == "on"
        
        chore_data = {
            "title": title,
            "description": description or "",
            "reward": float(reward) if reward is not None else 0.0,
            "assignee_id": int(assignee_id) if assignee_id is not None else None,
            "is_recurring": is_recurring_bool,
            "frequency": frequency if is_recurring_bool else None,
        }
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
    
    # Check if assignee exists and is a child of the current user
    assignee = await user_repo.get(db, id=chore_data["assignee_id"])
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found"
        )
    
    if assignee.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only assign chores to your own children"
        )
    
    # Add creator_id to chore data
    chore_data["creator_id"] = current_user.id
    
    # Create chore
    chore = await chore_repo.create(db, obj_in=chore_data)
    return chore

@router.get("/", response_model=List[ChoreResponse])
async def read_chores(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chores based on user role."""
    if current_user.is_parent:
        # Parents see chores they created
        chores = await chore_repo.get_by_creator(db, creator_id=current_user.id)
    else:
        # Children see chores assigned to them
        chores = await chore_repo.get_by_assignee(db, assignee_id=current_user.id)
    
    return chores

@router.get("/{chore_id}", response_model=ChoreResponse)
async def read_chore(
    chore_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chore."""
    chore = await chore_repo.get(db, id=chore_id, eager_load_relations=["assignee", "creator"])
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
    current_user: User = Depends(get_current_user)
):
    """Update a chore."""
    chore = await chore_repo.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    # Only the creator (parent) can update chores
    if not current_user.is_parent or chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this chore"
        )
    
    updated_chore = await chore_repo.update(db, id=chore_id, obj_in=chore_in.dict(exclude_unset=True))
    return updated_chore

@router.delete("/{chore_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chore."""
    chore = await chore_repo.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    # Only the creator (parent) can delete chores
    if not current_user.is_parent or chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this chore"
        )
    
    await chore_repo.delete(db, id=chore_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{chore_id}/complete", response_model=ChoreResponse)
async def complete_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a chore as completed."""
    chore = await chore_repo.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    # Only the assignee can mark a chore as completed
    if chore.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assignee can mark a chore as completed"
        )
    
    if chore.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chore is already completed"
        )
    
    updated_chore = await chore_repo.mark_completed(db, chore_id=chore_id)
    return updated_chore

@router.post("/{chore_id}/approve", response_model=ChoreResponse)
async def approve_chore(
    chore_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a completed chore."""
    chore = await chore_repo.get(db, id=chore_id)
    if not chore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chore not found"
        )
    
    # Only the creator (parent) can approve chores
    if not current_user.is_parent or chore.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can approve chores"
        )
    
    if not chore.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chore must be completed before approval"
        )
    
    if chore.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chore is already approved"
        )
    
    updated_chore = await chore_repo.approve_chore(db, chore_id=chore_id)
    return updated_chore