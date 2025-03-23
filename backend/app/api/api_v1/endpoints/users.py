from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....db.base import get_db
from ....models.user import User
from ....schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve users.
    """
    # Placeholder - will implement actual database query later
    return []

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Create new user.
    """
    # Placeholder - will implement actual user creation later
    return {"id": 1, "username": user_in.username, "email": user_in.email, "is_parent": user_in.is_parent}