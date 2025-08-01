"""
Test script to verify balance calculations include reward adjustments.
"""
import asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import AsyncSessionLocal
from ..models.user import User
from ..models.chore import Chore
from ..models.reward_adjustment import RewardAdjustment
from ..repositories.user import UserRepository
from ..repositories.chore import ChoreRepository
from ..repositories.reward_adjustment import RewardAdjustmentRepository

async def main():
    """Test balance calculations with adjustments."""
    async with AsyncSessionLocal() as db:
        print("Testing balance calculation with adjustments...")
        
        # Initialize repositories
        user_repo = UserRepository()
        chore_repo = ChoreRepository()
        adjustment_repo = RewardAdjustmentRepository()
        
        # Find a test parent
        result = await db.execute(
            select(User).where(User.username == "testparent2", User.is_parent == True)
        )
        parent = result.scalars().first()
        
        if not parent:
            print("Error: Test parent not found. Please create a parent user first.")
            return
        
        print(f"Found parent: {parent.username} (ID: {parent.id})")
        
        # Get or create a test child
        children = await user_repo.get_children(db, parent_id=parent.id)
        
        if not children:
            print("No children found. Checking if testchild exists...")
            # Check if testchild exists but belongs to different parent
            result = await db.execute(
                select(User).where(User.username == "testchild")
            )
            existing_child = result.scalars().first()
            
            if existing_child:
                print(f"Found existing testchild (ID: {existing_child.id}), updating parent...")
                existing_child.parent_id = parent.id
                await db.commit()
                child = existing_child
            else:
                print("Creating new test child...")
                child_data = {
                    "username": "testchild",
                    "password": "password123",
                    "is_parent": False,
                    "parent_id": parent.id
                }
                child = await user_repo.create(db, obj_in=child_data)
            print(f"Using child: {child.username} (ID: {child.id})")
        else:
            child = children[0]
            print(f"Found child: {child.username} (ID: {child.id})")
        
        # Create some approved chores for the child
        print("\nCreating test chores...")
        
        # Check if chores already exist
        existing_chores = await chore_repo.get_by_assignee(db, assignee_id=child.id)
        approved_chores = [c for c in existing_chores if c.is_completed and c.is_approved]
        
        if len(approved_chores) < 2:
            # Create more chores
            for i in range(2):
                chore_data = {
                    "title": f"Test Chore {i+1}",
                    "description": f"Test chore for balance calculation",
                    "reward": Decimal("5.00"),
                    "is_range_reward": False,
                    "cooldown_days": 0,
                    "is_recurring": False,
                    "creator_id": parent.id,
                    "assignee_id": child.id,
                    "is_completed": True,
                    "is_approved": True,
                    "is_disabled": False
                }
                chore = await chore_repo.create(db, obj_in=chore_data)
                print(f"  Created chore: {chore.title} - ${chore.reward}")
        
        # Calculate current earnings
        all_chores = await chore_repo.get_by_assignee(db, assignee_id=child.id)
        approved_chores = [c for c in all_chores if c.is_completed and c.is_approved]
        total_earned = Decimal(str(sum(c.reward for c in approved_chores)))
        print(f"\nTotal earned from chores: ${total_earned}")
        
        # Get current adjustments
        current_adjustments = await adjustment_repo.calculate_total_adjustments(db, child_id=child.id)
        print(f"Current adjustments: ${current_adjustments}")
        
        # Create a new positive adjustment
        print("\nCreating positive adjustment...")
        adjustment1 = RewardAdjustment(
            child_id=child.id,
            parent_id=parent.id,
            amount=Decimal("10.00"),
            reason="Bonus for helping with extra chores"
        )
        db.add(adjustment1)
        await db.commit()
        print(f"  Added adjustment: +${adjustment1.amount} - {adjustment1.reason}")
        
        # Create a negative adjustment
        print("\nCreating negative adjustment...")
        adjustment2 = RewardAdjustment(
            child_id=child.id,
            parent_id=parent.id,
            amount=Decimal("-3.50"),
            reason="Deduction for not completing homework"
        )
        db.add(adjustment2)
        await db.commit()
        print(f"  Added adjustment: ${adjustment2.amount} - {adjustment2.reason}")
        
        # Calculate new total adjustments
        total_adjustments = await adjustment_repo.calculate_total_adjustments(db, child_id=child.id)
        print(f"\nNew total adjustments: ${total_adjustments}")
        
        # Calculate final balance
        paid_out = Decimal("0.00")  # Assuming no payments yet
        balance_due = total_earned + total_adjustments - paid_out
        
        print("\n=== BALANCE SUMMARY ===")
        print(f"Chore Earnings: ${total_earned}")
        print(f"Adjustments: ${total_adjustments}")
        print(f"Paid Out: ${paid_out}")
        print(f"Balance Due: ${balance_due}")
        
        # Test the allowance summary endpoint would show
        print("\n=== Expected Allowance Summary Data ===")
        print({
            "id": child.id,
            "username": child.username,
            "completed_chores": len(approved_chores),
            "total_earned": f"{total_earned:.2f}",
            "total_adjustments": f"{total_adjustments:.2f}",
            "paid_out": f"{paid_out:.2f}",
            "balance_due": f"{balance_due:.2f}"
        })

if __name__ == "__main__":
    asyncio.run(main())