from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime

class ChoreBase(BaseModel):
    """Base chore schema with common fields."""
    title: str = Field(
        ...,
        description="Title of the chore",
        min_length=1,
        max_length=200,
        json_schema_extra={"example": "Clean the kitchen"}
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description of what needs to be done",
        max_length=1000,
        json_schema_extra={"example": "Wipe counters, wash dishes, sweep floor"}
    )
    reward: float = Field(
        0.0,
        description="Fixed reward amount (used when is_range_reward is false)",
        ge=0,
        le=1000,
        json_schema_extra={"example": 5.0}
    )
    min_reward: Optional[float] = Field(
        None,
        description="Minimum reward for range-based rewards",
        ge=0,
        le=1000,
        json_schema_extra={"example": 3.0}
    )
    max_reward: Optional[float] = Field(
        None,
        description="Maximum reward for range-based rewards",
        ge=0,
        le=1000,
        json_schema_extra={"example": 7.0}
    )
    is_range_reward: bool = Field(
        False,
        description="Whether this chore has a range-based reward (parent chooses amount during approval)",
        json_schema_extra={"example": False}
    )
    cooldown_days: int = Field(
        0,
        description="Days before the chore can be completed again (for recurring chores)",
        ge=0,
        le=365,
        json_schema_extra={"example": 7}
    )
    is_recurring: bool = Field(
        False,
        description="Whether this chore can be completed multiple times",
        json_schema_extra={"example": True}
    )
    frequency: Optional[str] = Field(
        None,
        description="Legacy field - use cooldown_days instead",
        deprecated=True
    )
    is_disabled: bool = Field(
        False,
        description="Whether the chore is disabled (soft delete)",
        json_schema_extra={"example": False}
    )
    
    @field_validator('max_reward')
    @classmethod
    def validate_reward_range(cls, v, info):
        if v is not None and 'min_reward' in info.data and info.data['min_reward'] is not None:
            if v < info.data['min_reward']:
                raise ValueError('max_reward must be greater than min_reward')
        return v

class ChoreCreate(ChoreBase):
    """Schema for creating a new chore."""
    assignee_id: int = Field(
        ...,
        description="ID of the child user who will be assigned this chore",
        json_schema_extra={"example": 2}
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Take out the trash",
                    "description": "Empty all wastebaskets and take bags to curb",
                    "reward": 2.0,
                    "is_range_reward": False,
                    "is_recurring": True,
                    "cooldown_days": 1,
                    "assignee_id": 2,
                    "recurrence_type": "daily"
                },
                {
                    "title": "Mow the lawn",
                    "description": "Mow front and back lawn, edge walkways",
                    "min_reward": 10.0,
                    "max_reward": 20.0,
                    "is_range_reward": True,
                    "is_recurring": True,
                    "cooldown_days": 7,
                    "assignee_id": 3,
                    "recurrence_type": "weekly"
                }
            ]
        }
    )

class ChoreUpdate(BaseModel):
    """Schema for updating an existing chore (all fields optional)."""
    title: Optional[str] = Field(
        None,
        description="New title for the chore",
        min_length=1,
        max_length=200
    )
    description: Optional[str] = Field(
        None,
        description="New description",
        max_length=1000
    )
    reward: Optional[float] = Field(
        None,
        description="New fixed reward amount",
        ge=0,
        le=1000
    )
    min_reward: Optional[float] = Field(
        None,
        description="New minimum reward for range",
        ge=0,
        le=1000
    )
    max_reward: Optional[float] = Field(
        None,
        description="New maximum reward for range",
        ge=0,
        le=1000
    )
    is_range_reward: Optional[bool] = Field(
        None,
        description="Change reward type"
    )
    cooldown_days: Optional[int] = Field(
        None,
        description="New cooldown period",
        ge=0,
        le=365
    )
    is_recurring: Optional[bool] = Field(
        None,
        description="Change recurring status"
    )
    frequency: Optional[str] = Field(
        None,
        description="Legacy field",
        deprecated=True
    )
    assignee_id: Optional[int] = Field(
        None,
        description="Reassign to different child"
    )
    is_disabled: Optional[bool] = Field(
        None,
        description="Enable/disable the chore"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Updated chore title",
                    "reward": 7.5
                },
                {
                    "assignee_id": 3,
                    "cooldown_days": 14
                }
            ]
        }
    )

class ChoreResponse(ChoreBase):
    """Schema for chore responses including all fields."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Clean Room",
                "description": "Vacuum, dust, and organize",
                "reward": 5.0,
                "is_range_reward": False,
                "cooldown_days": 7,
                "is_recurring": True,
                "assignee_id": 2,
                "creator_id": 1,
                "is_completed": False,
                "is_approved": False,
                "is_disabled": False,
                "created_at": "2024-12-20T10:00:00",
                "updated_at": "2024-12-20T10:00:00"
            }
        }
    )
    
    id: int = Field(
        ...,
        description="Unique chore ID"
    )
    assignee_id: Optional[int] = Field(
        ...,
        description="ID of assigned child (can be null if unassigned)"
    )
    creator_id: int = Field(
        ...,
        description="ID of parent who created the chore"
    )
    is_completed: bool = Field(
        False,
        description="Whether child has marked as complete"
    )
    is_approved: bool = Field(
        False,
        description="Whether parent has approved completion"
    )
    completion_date: Optional[datetime] = Field(
        None,
        description="When the chore was last completed"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="When the chore was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When the chore was last updated"
    )

class ChoreComplete(BaseModel):
    """Schema for marking a chore as complete."""
    is_completed: bool = Field(
        True,
        description="Mark chore as completed (always true)",
        json_schema_extra={"example": True}
    )

class ChoreApprove(BaseModel):
    """Schema for approving a completed chore."""
    is_approved: bool = Field(
        True,
        description="Approve the chore (always true)",
        json_schema_extra={"example": True}
    )
    reward_value: Optional[float] = Field(
        None,
        description="Exact reward amount for range-based rewards (must be between min_reward and max_reward)",
        ge=0,
        le=1000,
        json_schema_extra={"example": 5.0}
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "is_approved": True,
                    "reward_value": 15.0,
                    "_comment": "For range-based reward chore"
                },
                {
                    "is_approved": True,
                    "_comment": "For fixed reward chore (reward_value not needed)"
                }
            ]
        }
    )

class ChoreDisable(BaseModel):
    """Schema for disabling a chore."""
    is_disabled: bool = Field(
        True,
        description="Disable the chore (always true)",
        json_schema_extra={"example": True}
    )