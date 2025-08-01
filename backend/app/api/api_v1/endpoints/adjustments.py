from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from ....db.base import get_db
from ....schemas.reward_adjustment import RewardAdjustmentCreate, RewardAdjustmentResponse
from ....dependencies.auth import get_current_user
from ....dependencies.services import RewardAdjustmentServiceDep
from ....models.user import User
from ....middleware.rate_limit import limit_api_endpoint_default, limit_create

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Standardized error response format
def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = {
        "error": {
            "code": error_code,
            "message": message
        }
    }
    if details:
        response["error"]["details"] = details
    return response


@router.post(
    "/",
    response_model=RewardAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reward adjustment",
    description="""
    Create a reward adjustment for a child's balance.
    
    **Access**: Parents only
    
    **Adjustment Types**:
    - **Positive adjustments**: Bonus rewards (e.g., +$5.00 for extra help)
    - **Negative adjustments**: Deductions (e.g., -$3.00 for penalty)
    
    **Business Rules**:
    - Only parents can create adjustments
    - Parents can only adjust their own children's rewards
    - Amount must be non-zero (range: -999.99 to 999.99)
    - Reason is required (3-500 characters)
    
    Rate limited to 30 requests per minute.
    """,
    responses={
        201: {
            "description": "Adjustment created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "child_id": 2,
                        "parent_id": 1,
                        "amount": "5.00",
                        "reason": "Bonus for extra help with groceries",
                        "created_at": "2024-01-01T10:00:00"
                    }
                }
            }
        },
        400: {
            "description": "Invalid adjustment data",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "INVALID_ADJUSTMENT",
                        "Invalid adjustment data provided",
                        {"field": "amount", "issue": "Amount cannot be zero"}
                    )
                }
            }
        },
        403: {
            "description": "Forbidden - not a parent or not your child",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "FORBIDDEN",
                        "You do not have permission to adjust this child's rewards"
                    )
                }
            }
        },
        404: {
            "description": "Child not found",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "NOT_FOUND",
                        "Child user not found",
                        {"child_id": 999}
                    )
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "VALIDATION_ERROR",
                        "Request validation failed",
                        {"errors": [{"field": "amount", "message": "ensure this value is not equal to 0"}]}
                    )
                }
            }
        }
    }
)
@limit_create
async def create_adjustment(
    request: Request,
    adjustment_data: RewardAdjustmentCreate,
    service: RewardAdjustmentServiceDep,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RewardAdjustmentResponse:
    """Create a new reward adjustment."""
    try:
        logger.info(
            f"Creating adjustment: user_id={current_user.id}, "
            f"child_id={adjustment_data.child_id}, amount={adjustment_data.amount}"
        )
        
        adjustment = await service.create_adjustment(
            db,
            adjustment_data=adjustment_data,
            current_user_id=current_user.id
        )
        
        logger.info(f"Successfully created adjustment: id={adjustment.id}")
        
        # Don't include relationships to avoid lazy loading issues
        return RewardAdjustmentResponse(
            id=adjustment.id,
            child_id=adjustment.child_id,
            parent_id=adjustment.parent_id,
            amount=adjustment.amount,
            reason=adjustment.reason,
            created_at=adjustment.created_at
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
        
    except ValidationError as e:
        logger.warning(f"Validation error creating adjustment: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=create_error_response(
                "VALIDATION_ERROR",
                "Request validation failed",
                {"errors": e.errors()}
            )
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database error creating adjustment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "DATABASE_ERROR",
                "An error occurred while saving the adjustment"
            )
        )
        
    except Exception as e:
        logger.error(f"Unexpected error creating adjustment: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "INTERNAL_ERROR",
                "An unexpected error occurred"
            )
        )


@router.get(
    "/child/{child_id}",
    response_model=List[RewardAdjustmentResponse],
    summary="Get adjustments for a child",
    description="""
    Get all reward adjustments for a specific child.
    
    **Access**: Parents only (for their own children)
    
    **Query Parameters**:
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum number of records to return (default: 100, max: 100)
    
    Results are ordered by creation date (newest first).
    
    Rate limited to 60 requests per minute.
    """,
    responses={
        200: {
            "description": "List of adjustments",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 2,
                            "child_id": 2,
                            "parent_id": 1,
                            "amount": "-3.50",
                            "reason": "Deduction for not completing homework",
                            "created_at": "2024-01-02T15:30:00"
                        },
                        {
                            "id": 1,
                            "child_id": 2,
                            "parent_id": 1,
                            "amount": "10.00",
                            "reason": "Bonus for extra chores",
                            "created_at": "2024-01-01T10:00:00"
                        }
                    ]
                }
            }
        },
        403: {
            "description": "Forbidden - not authorized to view these adjustments",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "FORBIDDEN",
                        "You do not have permission to view this child's adjustments"
                    )
                }
            }
        },
        404: {
            "description": "Child not found",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "NOT_FOUND",
                        "Child user not found",
                        {"child_id": 999}
                    )
                }
            }
        }
    }
)
@limit_api_endpoint_default
async def get_child_adjustments(
    request: Request,
    child_id: int,
    service: RewardAdjustmentServiceDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[RewardAdjustmentResponse]:
    """Get all adjustments for a specific child."""
    try:
        logger.info(
            f"Getting adjustments: user_id={current_user.id}, "
            f"child_id={child_id}, skip={skip}, limit={limit}"
        )
        
        adjustments = await service.get_child_adjustments(
            db,
            child_id=child_id,
            current_user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        logger.info(f"Retrieved {len(adjustments)} adjustments for child_id={child_id}")
        
        return [
            RewardAdjustmentResponse(
                id=adj.id,
                child_id=adj.child_id,
                parent_id=adj.parent_id,
                amount=adj.amount,
                reason=adj.reason,
                created_at=adj.created_at
            ) for adj in adjustments
        ]
        
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting adjustments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "DATABASE_ERROR",
                "An error occurred while retrieving adjustments"
            )
        )
        
    except Exception as e:
        logger.error(f"Unexpected error getting adjustments: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "INTERNAL_ERROR",
                "An unexpected error occurred"
            )
        )


@router.get(
    "/total/{child_id}",
    response_model=dict,
    summary="Get total adjustments for a child",
    description="""
    Get the total sum of all adjustments for a specific child.
    
    **Access**: Parents only (for their own children)
    
    This endpoint is useful for quickly checking the net adjustment amount
    without fetching all individual adjustment records.
    
    Rate limited to 60 requests per minute.
    """,
    responses={
        200: {
            "description": "Total adjustment amount",
            "content": {
                "application/json": {
                    "example": {
                        "child_id": 2,
                        "total_adjustments": "6.50",
                        "currency": "USD"
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - not authorized to view this total",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "FORBIDDEN",
                        "You do not have permission to view this child's adjustment total"
                    )
                }
            }
        },
        404: {
            "description": "Child not found",
            "content": {
                "application/json": {
                    "example": create_error_response(
                        "NOT_FOUND",
                        "Child user not found",
                        {"child_id": 999}
                    )
                }
            }
        }
    }
)
@limit_api_endpoint_default
async def get_child_adjustment_total(
    request: Request,
    child_id: int,
    service: RewardAdjustmentServiceDep,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get total adjustments for a specific child."""
    try:
        logger.info(
            f"Getting total adjustments: user_id={current_user.id}, child_id={child_id}"
        )
        
        total = await service.get_total_adjustments(
            db,
            child_id=child_id,
            current_user_id=current_user.id
        )
        
        logger.info(f"Total adjustments for child_id={child_id}: {total}")
        
        return {
            "child_id": child_id,
            "total_adjustments": str(total),
            "currency": "USD"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting total adjustments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "DATABASE_ERROR",
                "An error occurred while calculating total adjustments"
            )
        )
        
    except Exception as e:
        logger.error(f"Unexpected error getting total adjustments: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                "INTERNAL_ERROR",
                "An unexpected error occurred"
            )
        )