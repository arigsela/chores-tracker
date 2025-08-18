#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.db.base import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.models.chore import Chore
from sqlalchemy import select

async def debug_makoto_chores():
    """Debug makoto's chores and their reward values"""
    
    async with AsyncSessionLocal() as session:
        try:
            # First, verify makoto exists
            makoto_query = select(User).where(User.id == 37)
            makoto_result = await session.execute(makoto_query)
            makoto = makoto_result.scalar_one_or_none()
            
            if not makoto:
                print("Error: makoto user (ID 37) not found!")
                return False
                
            print(f"Found user: {makoto.username} (ID: {makoto.id})")
            
            # Find all chores assigned to makoto
            chores_query = select(Chore).where(Chore.assignee_id == 37)
            chores_result = await session.execute(chores_query)
            all_chores = chores_result.scalars().all()
            
            print(f"\nFound {len(all_chores)} total chores for makoto")
            print("=" * 80)
            
            total_expected = 0
            total_backend_calculation = 0
            
            for i, chore in enumerate(all_chores, 1):
                print(f"\nChore {i}:")
                print(f"  ID: {chore.id}")
                print(f"  Title: {chore.title}")
                print(f"  reward: {chore.reward}")
                print(f"  approval_reward: {chore.approval_reward}")
                print(f"  is_range_reward: {chore.is_range_reward}")
                print(f"  min_reward: {chore.min_reward}")
                print(f"  max_reward: {chore.max_reward}")
                print(f"  is_completed: {chore.is_completed}")
                print(f"  is_approved: {chore.is_approved}")
                print(f"  completion_date: {chore.completion_date}")
                print(f"  created_at: {chore.created_at}")
                
                # Calculate what the backend would use
                backend_amount = 0
                if chore.is_completed and chore.is_approved:
                    if chore.approval_reward is not None:
                        backend_amount = chore.approval_reward
                    else:
                        backend_amount = chore.reward or 0
                    total_backend_calculation += backend_amount
                    
                    # What we expect based on the test
                    if "Test Chore 1" in chore.title:
                        total_expected += 1
                        print(f"  Expected: $1.00, Backend will use: ${backend_amount}")
                    elif "Test Chore 2" in chore.title:
                        total_expected += 2
                        print(f"  Expected: $2.00, Backend will use: ${backend_amount}")
                    elif "Test Chore 3" in chore.title:
                        total_expected += 3
                        print(f"  Expected: $3.00, Backend will use: ${backend_amount}")
                    elif "Test Chore 4" in chore.title:
                        total_expected += 3  # Range reward set to $3
                        print(f"  Expected: $3.00 (range set), Backend will use: ${backend_amount}")
                    else:
                        print(f"  Unknown test chore, Backend will use: ${backend_amount}")
                else:
                    print(f"  Status: Not completed or not approved")
            
            print("\n" + "=" * 80)
            print(f"SUMMARY:")
            print(f"Total expected: ${total_expected}")
            print(f"Total backend calculation: ${total_backend_calculation}")
            print(f"Difference: ${total_expected - total_backend_calculation}")
            
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(debug_makoto_chores())
    if success:
        print("\n✅ Debug completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Debug failed")
        sys.exit(1)