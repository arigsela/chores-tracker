from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime

class PaymentBase(BaseModel):
    """Base payment schema with common fields."""
    amount: float = Field(
        ...,
        description="Payment amount (positive for adding to balance, negative for deductions)",
        json_schema_extra={"example": 10.50}
    )
    description: str = Field(
        ...,
        description="Description of the payment or adjustment",
        json_schema_extra={"example": "Weekly allowance payment"}
    )
    is_adjustment: bool = Field(
        False,
        description="Whether this is a manual adjustment (true) or a payment (false)",
        json_schema_extra={"example": False}
    )

class PaymentCreate(PaymentBase):
    """Schema for creating a new payment."""
    child_id: int = Field(
        ...,
        description="ID of the child receiving the payment",
        json_schema_extra={"example": 2}
    )

class PaymentResponse(PaymentBase):
    """Schema for payment responses including all fields."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "amount": 10.50,
                "description": "Weekly allowance payment",
                "is_adjustment": False,
                "created_at": "2025-07-30T14:30:00",
                "child_id": 2,
                "parent_id": 1
            }
        }
    )
    
    id: int = Field(
        ...,
        description="Unique payment ID",
        json_schema_extra={"example": 1}
    )
    created_at: datetime = Field(
        ...,
        description="When the payment was created",
        json_schema_extra={"example": "2025-07-30T14:30:00"}
    )
    child_id: int = Field(
        ...,
        description="ID of the child receiving the payment",
        json_schema_extra={"example": 2}
    )
    parent_id: int = Field(
        ...,
        description="ID of the parent making the payment",
        json_schema_extra={"example": 1}
    )

class AdjustmentCreate(PaymentBase):
    """Schema for creating a manual balance adjustment."""
    child_id: int = Field(
        ...,
        description="ID of the child to adjust balance for",
        json_schema_extra={"example": 2}
    )
    is_adjustment: Literal[True] = Field(
        True,
        description="Always true for adjustments",
        json_schema_extra={"example": True}
    )