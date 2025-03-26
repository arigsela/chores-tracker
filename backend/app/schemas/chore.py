from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChoreBase(BaseModel):
    title: str
    description: Optional[str] = None
    reward: float = 0.0
    min_reward: Optional[float] = None
    max_reward: Optional[float] = None
    is_range_reward: bool = False
    cooldown_days: int = 0
    is_recurring: bool = False
    frequency: Optional[str] = None  # legacy field
    is_disabled: bool = False

class ChoreCreate(ChoreBase):
    assignee_id: int

class ChoreUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reward: Optional[float] = None
    min_reward: Optional[float] = None
    max_reward: Optional[float] = None
    is_range_reward: Optional[bool] = None
    cooldown_days: Optional[int] = None
    is_recurring: Optional[bool] = None
    frequency: Optional[str] = None
    assignee_id: Optional[int] = None
    is_disabled: Optional[bool] = None

class ChoreResponse(ChoreBase):
    id: int
    assignee_id: int
    creator_id: int
    is_completed: bool = False
    is_approved: bool = False
    completion_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ChoreComplete(BaseModel):
    is_completed: bool = True

class ChoreApprove(BaseModel):
    is_approved: bool = True
    reward_value: Optional[float] = None  # For approving range-based rewards

class ChoreDisable(BaseModel):
    is_disabled: bool = True