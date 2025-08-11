#!/usr/bin/env python3
"""
Create demo children for testing Phase 4.3
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from backend.app.db.base import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.core.security.password import get_password_hash

async def create_demo_children():
    """Create demo children for the demoparent user"""
    async with AsyncSessionLocal() as db:
        # Find demoparent
        result = await db.execute(select(User).where(User.username == "demoparent"))
        parent = result.scalar_one_or_none()
        
        if not parent:
            print("Error: demoparent user not found!")
            return
        
        print(f"Found demoparent with ID: {parent.id}")
        
        # Create demochild1
        result = await db.execute(select(User).where(User.username == "demochild1"))
        existing_child1 = result.scalar_one_or_none()
        
        if not existing_child1:
            child1 = User(
                username="demochild1",
                hashed_password=get_password_hash("password123"),
                is_parent=False,
                is_active=True,
                parent_id=parent.id
            )
            db.add(child1)
            await db.commit()
            await db.refresh(child1)
            print(f"✅ Created demochild1 with ID: {child1.id}")
        else:
            print("demochild1 already exists")
        
        # Create demochild2
        result = await db.execute(select(User).where(User.username == "demochild2"))
        existing_child2 = result.scalar_one_or_none()
        
        if not existing_child2:
            child2 = User(
                username="demochild2",
                hashed_password=get_password_hash("password123"),
                is_parent=False,
                is_active=True,
                parent_id=parent.id
            )
            db.add(child2)
            await db.commit()
            await db.refresh(child2)
            print(f"✅ Created demochild2 with ID: {child2.id}")
        else:
            print("demochild2 already exists")
        
        print("\nDemo children created successfully!")

if __name__ == "__main__":
    print("Creating demo children for testing...")
    asyncio.run(create_demo_children())