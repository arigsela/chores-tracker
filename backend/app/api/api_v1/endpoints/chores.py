from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....db.base import get_db
from ....models.chore import Chore
from ....schemas.chore import ChoreCreate, ChoreResponse

router = APIRouter()

@router.get("/", response_model=List[ChoreResponse])
async def read_chores(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve chores.
    """
    # Placeholder - will implement actual database query later
    return []

@router.post("/", response_model=ChoreResponse, status_code=status.HTTP_201_CREATED)
async def create_chore(
    chore_in: ChoreCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Create new chore.
    """
    # Placeholder - will implement actual chore creation later
    return {
        "id": 1, 
        "title": chore_in.title, 
        "description": chore_in.description, 
        "reward": chore_in.reward,
        "is_recurring": chore_in.is_recurring,
        "frequency": chore_in.frequency,
        "is_completed": False,
        "is_approved": False
    }