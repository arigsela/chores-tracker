#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session_context
from app.models.chore import Chore
from app.models.user import User
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

async def reset_makoto_chores():
    """Remove all chores assigned to makoto (user ID 37)"""
    
    async with get_async_session_context() as session:
        try:
            # First, let's verify makoto exists
            makoto_query = select(User).where(User.id == 37)
            makoto_result = await session.execute(makoto_query)
            makoto = makoto_result.scalar_one_or_none()
            
            if not makoto:
                print("Error: makoto user (ID 37) not found!")
                return False
                
            print(f"Found user: {makoto.username} (ID: {makoto.id})")
            
            # Find all chores assigned to makoto
            chores_query = select(Chore).where(
                (Chore.assignee_id == 37) | (Chore.assigned_to_id == 37)
            )
            chores_result = await session.execute(chores_query)
            existing_chores = chores_result.scalars().all()
            
            print(f"Found {len(existing_chores)} existing chores for makoto")
            
            # Delete all chores for makoto
            if existing_chores:
                for chore in existing_chores:
                    print(f"Deleting chore: {chore.title} (ID: {chore.id})")
                    await session.delete(chore)
                
                await session.commit()
                print(f"Successfully deleted {len(existing_chores)} chores for makoto")
            else:
                print("No chores found for makoto")
            
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            await session.rollback()
            return False

if __name__ == "__main__":
    success = asyncio.run(reset_makoto_chores())
    if success:
        print("✅ Reset completed successfully")
        sys.exit(0)
    else:
        print("❌ Reset failed")
        sys.exit(1)