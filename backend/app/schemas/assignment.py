"""Pydantic schemas for ChoreAssignment model."""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime


class AssignmentBase(BaseModel):
    """Base assignment schema with common fields."""
    pass


class AssignmentCreate(BaseModel):
    """Schema for creating a new chore assignment."""
    assignee_id: int = Field(
        ...,
        description="ID of the child user who will be assigned this chore",
        gt=0,
        json_schema_extra={"example": 2}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assignee_id": 2
            }
        }
    )


class AssignmentResponse(AssignmentBase):
    """Schema for assignment responses including all fields."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "chore_id": 5,
                "assignee_id": 2,
                "is_completed": False,
                "is_approved": False,
                "completion_date": None,
                "approval_date": None,
                "approval_reward": None,
                "rejection_reason": None,
                "created_at": "2024-12-20T10:00:00",
                "updated_at": "2024-12-20T10:00:00"
            }
        }
    )

    id: int = Field(
        ...,
        description="Unique assignment ID"
    )
    chore_id: int = Field(
        ...,
        description="ID of the chore being assigned"
    )
    assignee_id: int = Field(
        ...,
        description="ID of the child user assigned to this chore"
    )
    is_completed: bool = Field(
        False,
        description="Whether child has marked this assignment as complete"
    )
    is_approved: bool = Field(
        False,
        description="Whether parent has approved this assignment completion"
    )
    completion_date: Optional[datetime] = Field(
        None,
        description="When the assignment was completed by the child"
    )
    approval_date: Optional[datetime] = Field(
        None,
        description="When the assignment was approved by the parent"
    )
    approval_reward: Optional[float] = Field(
        None,
        description="Final approved reward amount (for range-based rewards)",
        ge=0,
        le=1000
    )
    rejection_reason: Optional[str] = Field(
        None,
        description="Reason for rejecting the assignment completion",
        max_length=500
    )
    created_at: datetime = Field(
        ...,
        description="When the assignment was created"
    )
    updated_at: datetime = Field(
        ...,
        description="When the assignment was last updated"
    )


class AssignmentComplete(BaseModel):
    """Schema for marking an assignment as complete."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {}
        }
    )


class AssignmentApprove(BaseModel):
    """Schema for approving a completed assignment."""
    reward_value: Optional[float] = Field(
        None,
        description="Exact reward amount for range-based rewards (must be between chore's min_reward and max_reward). If not provided, uses the chore's fixed reward amount.",
        ge=0,
        le=1000,
        json_schema_extra={"example": 5.0}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reward_value": 5.0
            }
        }
    )


class AssignmentReject(BaseModel):
    """Schema for rejecting a completed assignment."""
    rejection_reason: str = Field(
        ...,
        description="Reason for rejecting the assignment completion",
        min_length=1,
        max_length=500,
        json_schema_extra={"example": "Please clean more thoroughly and organize items properly"}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rejection_reason": "Please clean more thoroughly and organize items properly"
            }
        }
    )


class AssignmentWithDetails(AssignmentResponse):
    """Assignment response with nested assignee and chore details."""
    assignee: Optional['UserResponse'] = Field(
        None,
        description="Details of the child user assigned to this chore (when eagerly loaded)"
    )

    # We don't include full chore details to avoid circular nesting issues
    # The chore_id field is sufficient for most use cases

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "chore_id": 5,
                "assignee_id": 2,
                "is_completed": True,
                "is_approved": False,
                "completion_date": "2024-12-20T14:30:00",
                "approval_date": None,
                "approval_reward": None,
                "rejection_reason": None,
                "created_at": "2024-12-20T10:00:00",
                "updated_at": "2024-12-20T14:30:00",
                "assignee": {
                    "id": 2,
                    "username": "alice",
                    "email": "alice@example.com",
                    "is_parent": False,
                    "is_active": True
                }
            }
        }
    )


# Avoid circular imports - import at end and rebuild
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user import UserResponse
    from .chore import ChoreResponse
else:
    from .user import UserResponse
    from .chore import ChoreResponse
    AssignmentWithDetails.model_rebuild()
