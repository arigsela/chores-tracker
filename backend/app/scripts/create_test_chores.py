#!/usr/bin/env python
"""Create test chores for demo users"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from backend.app.db.base import get_db, SessionLocal
from backend.app.repositories.user import UserRepository
from backend.app.repositories.chore import ChoreRepository
from backend.app.schemas.chore import ChoreCreate


async def create_test_chores():
    """Create test chores for the demo child user"""
    async with SessionLocal() as db:
        user_repo = UserRepository()
        chore_repo = ChoreRepository()
        
        # Get parent and child users
        parent = await user_repo.get_by_username(db, username="demoparent")
        child = await user_repo.get_by_username(db, username="demochild")
        
        if not parent:
            print("Parent user 'demoparent' not found!")
            return
            
        if not child:
            print("Child user 'demochild' not found!")
            return
            
        print(f"Found parent: {parent.username} (ID: {parent.id})")
        print(f"Found child: {child.username} (ID: {child.id})")
        
        # Check if chores already exist
        existing_chores = await chore_repo.get_by_child(db, child_id=child.id)
        if existing_chores:
            print(f"Child already has {len(existing_chores)} chores")
            return
        
        # Create test chores
        chores_data = [
            ChoreCreate(
                title="Clean Your Room",
                description="Make bed, organize toys, vacuum floor",
                reward=5.0,
                is_range_reward=False,
                assignee_id=child.id,
                is_recurring=True,
                cooldown_days=7
            ),
            ChoreCreate(
                title="Do Homework",
                description="Complete all homework assignments",
                reward=3.0,
                is_range_reward=False,
                assignee_id=child.id,
                is_recurring=True,
                cooldown_days=1
            ),
            ChoreCreate(
                title="Take Out Trash",
                description="Empty all wastebaskets and take to curb",
                is_range_reward=True,
                min_reward=2.0,
                max_reward=4.0,
                assignee_id=child.id,
                is_recurring=True,
                cooldown_days=3
            ),
            ChoreCreate(
                title="Feed the Pet",
                description="Give food and fresh water to the pet",
                reward=2.0,
                is_range_reward=False,
                assignee_id=child.id,
                is_recurring=True,
                cooldown_days=1
            ),
            ChoreCreate(
                title="Set the Table", 
                description="Set plates, utensils, and napkins for dinner",
                is_range_reward=True,
                min_reward=1.0,
                max_reward=3.0,
                assignee_id=child.id,
                is_recurring=True,
                cooldown_days=1
            )
        ]
        
        for chore_data in chores_data:
            chore = await chore_repo.create_with_creator(
                db,
                obj_in=chore_data,
                creator_id=parent.id
            )
            print(f"Created chore: {chore.title}")
        
        await db.commit()
        print(f"\nSuccessfully created {len(chores_data)} test chores for {child.username}!")


if __name__ == "__main__":
    asyncio.run(create_test_chores())