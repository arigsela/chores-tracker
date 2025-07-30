from fastapi import APIRouter, Depends, HTTPException, status, Response, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from ....db.base import get_db
from ....schemas.payment import PaymentCreate, PaymentResponse, AdjustmentCreate
from ....schemas.user import UserResponse
from ....models.user import User
from ....dependencies.auth import get_current_user
from ....dependencies.services import PaymentServiceDep, UserServiceDep
from ....core.unit_of_work import get_unit_of_work, UnitOfWork
from ....middleware.rate_limit import limit_api_endpoint, limit_create

router = APIRouter()


@router.post(
    "/record",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a payment to a child",
    description="""
    Record a payment made to a child (reducing their balance).
    
    **Access**: Parents only
    
    **Business rules**:
    - Only parents can record payments
    - Parents can only pay their own children
    - Payment amount must be positive
    - Payment amount cannot exceed the child's current balance
    """
)
@limit_create
async def record_payment(
    payment: PaymentCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
    payment_service: PaymentServiceDep = None
):
    """Record a payment to a child."""
    # Only parents can record payments
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can record payments"
        )
    
    # Process payment with balance check
    try:
        result = await payment_service.process_payment_with_balance_check(
            uow,
            parent_id=current_user.id,
            child_id=payment.child_id,
            amount=payment.amount,
            description=payment.description
        )
        
        return result["payment"]
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        # Log other exceptions and return a generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment: {str(e)}"
        )


@router.post(
    "/adjust",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or remove reward dollars manually",
    description="""
    Manually adjust a child's reward balance.
    
    **Access**: Parents only
    
    **Business rules**:
    - Only parents can adjust balances
    - Parents can only adjust for their own children
    - Amount can be positive (adding) or negative (removing)
    - Description must explain the reason for adjustment
    """
)
@limit_create
async def adjust_balance(
    adjustment: AdjustmentCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payment_service: PaymentServiceDep = None
):
    """Manually adjust a child's reward balance."""
    # Only parents can adjust balances
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can adjust balances"
        )
    
    # Create adjustment record
    try:
        adjustment = await payment_service.create_adjustment(
            db,
            parent_id=current_user.id,
            child_id=adjustment.child_id,
            amount=adjustment.amount,
            description=adjustment.description
        )
        
        return adjustment
    except HTTPException:
        # Re-raise HTTP exceptions from the service
        raise
    except Exception as e:
        # Log other exceptions and return a generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create adjustment: {str(e)}"
        )


@router.get(
    "/history/{child_id}",
    response_model=List[PaymentResponse],
    summary="Get payment history for a child",
    description="""
    Get the complete payment and adjustment history for a child.
    
    **Access**: Parents only (for their own children)
    
    **Returns**:
    - List of payment and adjustment records in chronological order
    - Includes both regular payments and manual adjustments
    """
)
@limit_api_endpoint
async def get_payment_history(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payment_service: PaymentServiceDep = None,
    user_service: UserServiceDep = None
):
    """Get payment history for a child."""
    # Only parents can view payment history
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view payment history"
        )
    
    # Verify child belongs to parent
    child = await user_service.get_user_by_id(db, id=child_id)
    if not child or child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or not your child"
        )
    
    # Get payment history
    try:
        payments = await payment_service.get_payment_history(db, child_id=child_id)
        return payments
    except Exception as e:
        # Log exception and return a generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment history: {str(e)}"
        )


@router.get(
    "/balance/{child_id}",
    summary="Get current balance for a child",
    description="""
    Get the current reward balance and details for a child.
    
    **Access**: Parents only (for their own children)
    
    **Returns**:
    - Total earned from completed chores
    - Total paid out in payments
    - Total adjustments (positive or negative)
    - Current balance
    """
)
@limit_api_endpoint
async def get_child_balance(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payment_service: PaymentServiceDep = None,
    user_service: UserServiceDep = None
):
    """Get current balance for a child."""
    # Only parents can view balances
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can view balances"
        )
    
    # Verify child belongs to parent
    child = await user_service.get_user_by_id(db, id=child_id)
    if not child or child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or not your child"
        )
    
    # Get balance details
    try:
        balance = await payment_service.get_child_balance(db, child_id=child_id)
        return balance
    except Exception as e:
        # Log exception and return a generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve balance: {str(e)}"
        )