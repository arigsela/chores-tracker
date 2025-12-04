from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Literal
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
    approval_reward: Optional[float] = Field(
        None,
        description="Final approved reward amount for range-based rewards",
        ge=0,
        le=1000,
        json_schema_extra={"example": 5.5}
    )
    rejection_reason: Optional[str] = Field(
        None,
        description="Reason for rejecting the chore completion",
        max_length=500,
        json_schema_extra={"example": "Please clean more thoroughly and organize items properly"}
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
    """Schema for creating a new chore with multi-assignment support."""
    assignment_mode: Literal['single', 'multi_independent', 'unassigned'] = Field(
        'single',
        description="Assignment mode: 'single' (one child), 'multi_independent' (multiple children, independent completion), 'unassigned' (pool, any child can claim)",
        json_schema_extra={"example": "single"}
    )
    assignee_ids: List[int] = Field(
        default_factory=list,
        description="List of child user IDs to assign this chore to. Required for 'single' and 'multi_independent' modes, must be empty for 'unassigned' mode.",
        json_schema_extra={"example": [2, 3]}
    )

    @field_validator('assignee_ids')
    @classmethod
    def validate_assignee_ids(cls, v, info):
        """Validate assignee_ids based on assignment_mode."""
        if 'assignment_mode' not in info.data:
            return v

        mode = info.data['assignment_mode']

        if mode == 'single':
            if len(v) != 1:
                raise ValueError("'single' assignment mode requires exactly 1 assignee_id")
        elif mode == 'multi_independent':
            if len(v) < 1:
                raise ValueError("'multi_independent' assignment mode requires at least 1 assignee_id")
        elif mode == 'unassigned':
            if len(v) != 0:
                raise ValueError("'unassigned' assignment mode must have 0 assignee_ids (empty list)")

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Take out the trash",
                "description": "Empty all wastebaskets and take bags to curb",
                "reward": 2.0,
                "is_recurring": True,
                "cooldown_days": 1,
                "assignment_mode": "single",
                "assignee_ids": [2]
            }
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
    is_disabled: Optional[bool] = Field(
        None,
        description="Enable/disable the chore"
    )
    assignee_ids: Optional[List[int]] = Field(
        None,
        description="Update the list of assignees for the chore. Only allowed for chores with no completed/approved assignments."
    )
    # Note: assignment_mode cannot be changed after creation

class ChoreResponse(ChoreBase):
    """Schema for chore responses with multi-assignment support."""
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
                "assignment_mode": "single",
                "creator_id": 1,
                "is_disabled": False,
                "created_at": "2024-12-20T10:00:00",
                "updated_at": "2024-12-20T10:00:00",
                "assignments": []
            }
        }
    )

    id: int = Field(
        ...,
        description="Unique chore ID"
    )
    assignment_mode: str = Field(
        ...,
        description="Assignment mode: 'single', 'multi_independent', or 'unassigned'"
    )
    creator_id: int = Field(
        ...,
        description="ID of parent who created the chore"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="When the chore was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="When the chore was last updated"
    )

    # Backward compatibility fields populated from assignment data
    is_completed: Optional[bool] = Field(
        None,
        description="Whether this specific assignment is completed (populated from assignment data for backward compatibility)"
    )
    is_approved: Optional[bool] = Field(
        None,
        description="Whether this specific assignment is approved (populated from assignment data for backward compatibility)"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="When this specific assignment was completed (populated from assignment data for backward compatibility)"
    )
    approved_at: Optional[datetime] = Field(
        None,
        description="When this specific assignment was approved (populated from assignment data for backward compatibility)"
    )

    # Assignment relationship (when eagerly loaded)
    assignments: List['AssignmentResponse'] = Field(
        default_factory=list,
        description="List of assignments for this chore (when eagerly loaded)"
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

class ChoreDisable(BaseModel):
    """Schema for disabling a chore."""
    is_disabled: bool = Field(
        True,
        description="Disable the chore (always true)",
        json_schema_extra={"example": True}
    )

class ChoreReject(BaseModel):
    """Schema for rejecting a completed chore."""
    rejection_reason: str = Field(
        ...,
        description="Reason for rejecting the chore completion",
        min_length=1,
        max_length=500,
        json_schema_extra={"example": "Please clean more thoroughly and organize items properly"}
    )

# Avoid circular imports - import at end and rebuild
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import UserResponse
    from .assignment import AssignmentResponse
else:
    from .user import UserResponse
    from .assignment import AssignmentResponse
    ChoreResponse.model_rebuild()