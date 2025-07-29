from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
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

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None)
    password: Optional[str] = Field(None, min_length=4)
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    """Schema for password reset requests."""
    new_password: str = Field(
        ...,
        description="New password for the user",
        min_length=4,
        json_schema_extra={"example": "NewSecurePass123"}
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