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
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "Example"},
                "error": None,
                "timestamp": "2024-12-20T10:00:00Z"
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "total": 50,
                "page": 1,
                "page_size": 10,
                "total_pages": 5,
                "error": None,
                "timestamp": "2024-12-20T10:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    details: Optional[Any] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Resource not found",
                "error_code": "NOT_FOUND",
                "details": {"resource_id": 123},
                "timestamp": "2024-12-20T10:00:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """Simple success response for operations without data."""
    success: bool = Field(True, description="Always true for success")
    message: str = Field(..., description="Success message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "timestamp": "2024-12-20T10:00:00Z"
            }
        }