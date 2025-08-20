"""
Activity schemas for API serialization.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .user import UserResponse


class ActivityBase(BaseModel):
    """Base activity schema."""
    
    activity_type: str = Field(
        ...,
        description="Type of activity (e.g., 'chore_completed', 'chore_approved')",
        min_length=1,
        max_length=50
    )
    description: str = Field(
        ...,
        description="Human-readable description of the activity",
        min_length=1,
        max_length=500
    )
    target_user_id: Optional[int] = Field(
        None,
        description="ID of target user (e.g., child for whom chore was approved)"
    )
    activity_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Activity-specific metadata"
    )


class ActivityCreate(ActivityBase):
    """Schema for creating activities."""
    
    user_id: int = Field(
        ...,
        gt=0,
        description="ID of user performing the activity (must be positive)"
    )


class ActivityResponse(ActivityBase):
    """Schema for activity responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(
        ...,
        gt=0,
        description="Unique activity ID (must be positive)"
    )
    user_id: int = Field(
        ...,
        gt=0,
        description="ID of user who performed the activity (must be positive)"
    )
    created_at: datetime = Field(
        ...,
        description="When the activity occurred"
    )
    
    # Optional relationships (populated when needed)
    user: Optional[UserResponse] = Field(
        None,
        description="User who performed the activity"
    )
    target_user: Optional[UserResponse] = Field(
        None,
        description="Target user of the activity"
    )


class ActivityListResponse(BaseModel):
    """Schema for paginated activity lists."""
    
    activities: list[ActivityResponse] = Field(
        ...,
        description="List of activities"
    )
    total_count: Optional[int] = Field(
        None,
        ge=0,
        description="Total number of activities (if available, must be non-negative)"
    )
    has_more: bool = Field(
        False,
        description="Whether there are more activities available"
    )


class ActivitySummaryResponse(BaseModel):
    """Schema for activity summary statistics."""
    
    activity_counts: Dict[str, int] = Field(
        ...,
        description="Count of activities by type (all counts must be non-negative)"
    )
    total_activities: int = Field(
        ...,
        ge=0,
        description="Total number of activities (must be non-negative)"
    )
    period_days: int = Field(
        ...,
        gt=0,
        description="Number of days the summary covers (must be positive)"
    )
    
    @field_validator('activity_counts')
    @classmethod
    def validate_activity_counts(cls, v):
        """Validate that all activity counts are non-negative."""
        if isinstance(v, dict):
            for key, count in v.items():
                if isinstance(count, int) and count < 0:
                    raise ValueError(f"Activity count for '{key}' must be non-negative, got {count}")
        return v


# Common activity type constants for documentation
class ActivityTypes:
    """Constants for activity types."""
    
    CHORE_COMPLETED = "chore_completed"
    CHORE_APPROVED = "chore_approved"
    CHORE_REJECTED = "chore_rejected"
    CHORE_CREATED = "chore_created"
    ADJUSTMENT_APPLIED = "adjustment_applied"
    
    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get all activity types."""
        return [
            cls.CHORE_COMPLETED,
            cls.CHORE_APPROVED,
            cls.CHORE_REJECTED,
            cls.CHORE_CREATED,
            cls.ADJUSTMENT_APPLIED
        ]
    
    @classmethod
    def get_type_descriptions(cls) -> Dict[str, str]:
        """Get descriptions for each activity type."""
        return {
            cls.CHORE_COMPLETED: "Child completed a chore",
            cls.CHORE_APPROVED: "Parent approved a completed chore",
            cls.CHORE_REJECTED: "Parent rejected a completed chore",
            cls.CHORE_CREATED: "Parent created a new chore",
            cls.ADJUSTMENT_APPLIED: "Parent applied a reward adjustment"
        }