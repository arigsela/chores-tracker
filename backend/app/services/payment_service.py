"""
Payment service with business logic for payment operations.
"""
from typing import Optional, List, Dict, Any, Union
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import Payment
from ..models.user import User
from ..repositories.payment import PaymentRepository
from ..repositories.user import UserRepository
from ..repositories.chore import ChoreRepository
from ..core.unit_of_work import UnitOfWork
from .base import BaseService


class PaymentService(BaseService[Payment, PaymentRepository]):
    """Service for payment-related business logic."""
    
    def __init__(self):
        """Initialize payment service."""
        super().__init__(PaymentRepository())
        self.user_repo = UserRepository()
        self.chore_repo = ChoreRepository()
    
    async def create_payment(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int,
        amount: float,
        description: str
    ) -> Payment:
        """
        Create a new payment record.
        
        Business rules:
        - Only parents can create payments
        - Parents can only pay their own children
        - Payment amount must be positive
        """
        # Validate parent-child relationship
        child = await self.user_repo.get(db, id=child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        if child.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only make payments to your own children"
            )
        
        # Validate payment amount
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be positive"
            )
        
        # Create payment record - using negative amount since it reduces the balance
        payment_data = {
            "amount": -amount,  # Negative because it's reducing balance
            "description": description,
            "is_adjustment": False,
            "child_id": child_id,
            "parent_id": parent_id
        }
        
        return await self.repository.create(db, obj_in=payment_data)
    
    async def create_adjustment(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int,
        amount: float,
        description: str
    ) -> Payment:
        """
        Create a manual balance adjustment.
        
        Business rules:
        - Only parents can create adjustments
        - Parents can only adjust balances for their own children
        - Amount can be positive (add to balance) or negative (subtract from balance)
        """
        # Validate parent-child relationship
        child = await self.user_repo.get(db, id=child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        if child.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only adjust balances for your own children"
            )
        
        # Create adjustment record
        adjustment_data = {
            "amount": amount,  # Can be positive or negative
            "description": description,
            "is_adjustment": True,
            "child_id": child_id,
            "parent_id": parent_id
        }
        
        return await self.repository.create(db, obj_in=adjustment_data)
    
    async def get_child_balance(
        self,
        db: AsyncSession,
        *,
        child_id: int
    ) -> Dict[str, Any]:
        """
        Calculate the current balance for a child.
        
        Includes:
        - Total earned (from completed and approved chores)
        - Total paid (from payment records)
        - Total adjustments (from adjustment records)
        - Current balance
        """
        # Get total earned from chores
        chores = await self.chore_repo.get_by_assignee(db, assignee_id=child_id)
        total_earned = sum(c.reward for c in chores if c.is_completed and c.is_approved)
        
        # Get total payments and adjustments
        total_payments = await self.repository.get_total_payments(db, child_id=child_id)
        total_adjustments = await self.repository.get_total_adjustments(db, child_id=child_id)
        
        # Calculate current balance
        current_balance = total_earned + total_payments + total_adjustments
        
        return {
            "total_earned": total_earned,
            "total_paid": abs(total_payments),  # Convert to positive for display
            "total_adjustments": total_adjustments,
            "current_balance": current_balance
        }
    
    async def get_payment_history(
        self,
        db: AsyncSession,
        *,
        child_id: int
    ) -> List[Payment]:
        """Get payment history for a child."""
        return await self.repository.get_by_child(db, child_id=child_id)
    
    async def process_payment_with_balance_check(
        self,
        uow: UnitOfWork,
        *,
        parent_id: int,
        child_id: int,
        amount: float,
        description: str
    ) -> Dict[str, Any]:
        """
        Process a payment with balance check in a single transaction.
        
        Business rules:
        - Only parents can create payments
        - Parents can only pay their own children
        - Payment amount must be positive
        - Cannot pay more than the current balance
        
        Returns the payment record and updated balance information.
        """
        async with uow:
            # Validate parent-child relationship
            child = await uow.users.get(id=child_id)
            if not child:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Child not found"
                )
            
            if child.parent_id != parent_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only make payments to your own children"
                )
            
            # Validate payment amount
            if amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment amount must be positive"
                )
            
            # Get current balance
            chores = await uow.chores.get_by_assignee(assignee_id=child_id)
            total_earned = sum(c.reward for c in chores if c.is_completed and c.is_approved)
            
            total_payments = await uow.payments.get_total_payments(child_id=child_id)
            total_adjustments = await uow.payments.get_total_adjustments(child_id=child_id)
            
            current_balance = total_earned + total_payments + total_adjustments
            
            # Check if payment exceeds balance
            if amount > current_balance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment amount (${amount}) exceeds current balance (${current_balance})"
                )
            
            # Create payment record
            payment_data = {
                "amount": -amount,  # Negative because it's reducing balance
                "description": description,
                "is_adjustment": False,
                "child_id": child_id,
                "parent_id": parent_id
            }
            
            payment = await uow.payments.create(obj_in=payment_data)
            
            # Calculate new balance
            new_balance = current_balance - amount
            
            # Commit transaction
            await uow.commit()
            
            return {
                "payment": payment,
                "balance": {
                    "previous_balance": current_balance,
                    "payment_amount": amount,
                    "new_balance": new_balance
                }
            }