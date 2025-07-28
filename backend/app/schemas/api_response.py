"""Standardized API response schemas for v2 endpoints."""
from typing import TypeVar, Generic, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Generic type for response data
DataT = TypeVar('DataT')


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[DataT] = Field(None, description="Response data if successful")
    error: Optional[str] = Field(None, description="Error message if not successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"id": 1, "username": "john_doe", "is_parent": True},
                    "error": None,
                    "timestamp": "2024-01-28T10:00:00Z"
                },
                {
                    "success": False,
                    "data": None,
                    "error": "User not found",
                    "timestamp": "2024-01-28T10:00:00Z"
                }
            ]
        }
    }


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: List[DataT] = Field(default_factory=list, description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    error: Optional[str] = Field(None, description="Error message if not successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "title": "Clean Room",
                        "reward": 5.0,
                        "assignee_id": 2,
                        "is_completed": False
                    },
                    {
                        "id": 2,
                        "title": "Take Out Trash",
                        "reward": 3.0,
                        "assignee_id": 2,
                        "is_completed": True
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 10,
                "total_pages": 5,
                "error": None,
                "timestamp": "2024-01-28T10:00:00Z"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    details: Optional[Any] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error": "Authentication required",
                    "error_code": "UNAUTHORIZED",
                    "details": None,
                    "timestamp": "2024-01-28T10:00:00Z"
                },
                {
                    "success": False,
                    "error": "Validation error",
                    "error_code": "VALIDATION_ERROR", 
                    "details": {
                        "field_errors": [
                            {"field": "email", "message": "Invalid email format"},
                            {"field": "password", "message": "Password too short"}
                        ]
                    },
                    "timestamp": "2024-01-28T10:00:00Z"
                }
            ]
        }
    }


class SuccessResponse(BaseModel):
    """Simple success response for operations without data."""
    success: bool = Field(True, description="Always true for success")
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Chore disabled successfully",
                    "timestamp": "2024-01-28T10:00:00Z"
                },
                {
                    "success": True,
                    "message": "Password reset successfully",
                    "timestamp": "2024-01-28T10:00:00Z"
                }
            ]
        }
    }