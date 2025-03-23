from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChoreBase(BaseModel):
    title: str
    description: Optional[str] = None
    reward: float = 0.0
    is_recurring: bool = False
    frequency: Optional[str] = None  # daily, weekly, etc.

class ChoreCreate(ChoreBase):
    assignee_id: int

class ChoreUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reward: Optional[float] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[str] = None
    assignee_id: Optional[int] = None

class ChoreResponse(ChoreBase):
    id: int
    assignee_id: int
    creator_id: int
    is_completed: bool = False
    is_approved: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True