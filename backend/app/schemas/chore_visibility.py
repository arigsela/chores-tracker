"""Chore visibility schemas for request/response validation."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ChoreVisibilityBase(BaseModel):
    """Base schema for chore visibility."""
    model_config = ConfigDict(from_attributes=True)
    
    chore_id: int = Field(..., description="ID of the chore")
    user_id: int = Field(..., description="ID of the user")


class ChoreVisibilityCreate(ChoreVisibilityBase):
    """Schema for creating chore visibility record."""
    is_hidden: bool = Field(True, description="Whether the chore is hidden from this user")


class ChoreVisibilityUpdate(BaseModel):
    """Schema for updating chore visibility."""
    model_config = ConfigDict(from_attributes=True)
    
    is_hidden: bool = Field(..., description="Whether the chore is hidden from this user")


class ChoreVisibilityBulkUpdate(BaseModel):
    """Schema for bulk updating chore visibility for multiple users."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "chore_id": 1,
                "hidden_from_users": [2, 3],
                "visible_to_users": [4, 5]
            }
        }
    )
    
    chore_id: int = Field(..., description="ID of the chore to update visibility for")
    hidden_from_users: List[int] = Field(default_factory=list, description="List of user IDs to hide the chore from")
    visible_to_users: List[int] = Field(default_factory=list, description="List of user IDs to show the chore to")


class ChoreVisibilityResponse(ChoreVisibilityBase):
    """Schema for chore visibility response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_hidden: bool
    created_at: datetime
    updated_at: datetime