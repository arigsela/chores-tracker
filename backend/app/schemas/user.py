from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List

class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(
        ...,
        description="Unique username for login",
        min_length=3,
        max_length=50,
        json_schema_extra={"example": "john_doe"}
    )
    is_parent: bool = Field(
        False,
        description="Whether this is a parent account (true) or child account (false)",
        json_schema_extra={"example": True}
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email address (required for parent accounts)",
        json_schema_extra={"example": "parent@example.com"}
    )

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(
        ...,
        description="User password (minimum 8 characters for parents, 4 for children)",
        min_length=4,
        json_schema_extra={"example": "SecurePassword123"}
    )
    parent_id: Optional[int] = Field(
        None,
        description="ID of the parent user (required for child accounts)",
        json_schema_extra={"example": 1}
    )

class UserLogin(BaseModel):
    """Schema for user login credentials."""
    username: str = Field(
        ...,
        description="Username for authentication",
        json_schema_extra={"example": "john_doe"}
    )
    password: str = Field(
        ...,
        description="User password",
        json_schema_extra={"example": "SecurePassword123"}
    )

class Token(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    token_type: str = Field(
        ...,
        description="Token type (always 'bearer')",
        json_schema_extra={"example": "bearer"}
    )

class UserResponse(UserBase):
    """Schema for user responses including all public fields."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "is_parent": True,
                "is_active": True,
                "parent_id": None
            }
        }
    )
    
    id: int = Field(
        ...,
        description="Unique user ID",
        json_schema_extra={"example": 1}
    )
    is_active: bool = Field(
        True,
        description="Whether the user account is active",
        json_schema_extra={"example": True}
    )
    parent_id: Optional[int] = Field(
        None,
        description="ID of parent user (null for parent accounts)",
        json_schema_extra={"example": None}
    )

class UserBalanceResponse(BaseModel):
    """Schema for user balance information."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "balance": 25.50,
                "total_earned": 45.00,
                "adjustments": 5.50,
                "paid_out": 25.00,
                "pending_chores_value": 10.00
            }
        }
    )
    
    balance: float = Field(
        ...,
        description="Current balance (total earned + adjustments - paid out)",
        json_schema_extra={"example": 25.50}
    )
    total_earned: float = Field(
        ...,
        description="Total amount earned from approved chores",
        json_schema_extra={"example": 45.00}
    )
    adjustments: float = Field(
        ...,
        description="Total adjustments (bonuses or deductions)",
        json_schema_extra={"example": 5.50}
    )
    paid_out: float = Field(
        ...,
        description="Total amount already paid out",
        json_schema_extra={"example": 25.00}
    )
    pending_chores_value: float = Field(
        0.0,
        description="Total value of chores pending approval",
        json_schema_extra={"example": 10.00}
    )


class ChildAllowanceSummary(BaseModel):
    """Per-child allowance summary for parent dashboard/API."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "username": "child_user",
                "completed_chores": 5,
                "total_earned": 25.50,
                "total_adjustments": -2.00,
                "paid_out": 0.00,
                "balance_due": 23.50
            }
        }
    )
    
    id: int = Field(
        ...,
        description="Child user ID",
        json_schema_extra={"example": 2}
    )
    username: str = Field(
        ...,
        description="Child username",
        json_schema_extra={"example": "child_user"}
    )
    completed_chores: int = Field(
        ...,
        description="Number of completed & approved chores",
        json_schema_extra={"example": 5}
    )
    total_earned: float = Field(
        ...,
        description="Total earned from approved chores",
        json_schema_extra={"example": 25.50}
    )
    total_adjustments: float = Field(
        ...,
        description="Sum of reward adjustments (bonuses/deductions)",
        json_schema_extra={"example": -2.00}
    )
    paid_out: float = Field(
        ...,
        description="Total amount paid out (currently 0 if not tracked)",
        json_schema_extra={"example": 0.00}
    )
    balance_due: float = Field(
        ...,
        description="Computed balance due to the child",
        json_schema_extra={"example": 23.50}
    )