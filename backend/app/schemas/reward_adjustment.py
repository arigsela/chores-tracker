from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

class RewardAdjustmentBase(BaseModel):
    """Base reward adjustment schema with common fields."""
    amount: Decimal = Field(
        ...,
        description="Adjustment amount (positive for bonus, negative for penalty)",
        ge=-999.99,
        le=999.99,
        decimal_places=2,
        json_schema_extra={"example": "5.00"}
    )
    reason: str = Field(
        ...,
        description="Reason for the adjustment",
        min_length=3,
        max_length=500,
        json_schema_extra={"example": "Bonus for completing extra chores"}
    )

class RewardAdjustmentCreate(RewardAdjustmentBase):
    """Schema for creating a new reward adjustment."""
    child_id: int = Field(
        ...,
        description="ID of the child receiving the adjustment",
        json_schema_extra={"example": 2}
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount_not_zero(cls, v):
        """Ensure amount is not zero."""
        if v == 0:
            raise ValueError('Adjustment amount cannot be zero')
        return v

class RewardAdjustmentResponse(RewardAdjustmentBase):
    """Schema for reward adjustment responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(
        ...,
        description="Unique adjustment ID",
        json_schema_extra={"example": 1}
    )
    child_id: int = Field(
        ...,
        description="ID of the child who received the adjustment",
        json_schema_extra={"example": 2}
    )
    parent_id: int = Field(
        ...,
        description="ID of the parent who created the adjustment",
        json_schema_extra={"example": 1}
    )
    created_at: datetime = Field(
        ...,
        description="When the adjustment was created",
        json_schema_extra={"example": "2024-01-01T10:00:00"}
    )
    
    # Optional related objects
    child: Optional['UserResponse'] = Field(
        None,
        description="Child user details"
    )
    parent: Optional['UserResponse'] = Field(
        None,
        description="Parent user details"
    )

# Avoid circular imports
from .user import UserResponse
RewardAdjustmentResponse.model_rebuild()