import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.db.base import AsyncSessionLocal
from backend.app.models.user import User
from sqlalchemy import select

async def list_users():
    """List all users in the database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found in the database.")
            return
            
        print("\nUsers in the database:")
        print("-" * 50)
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Is Parent: {user.is_parent}")
            print(f"Is Active: {user.is_active}")
            print(f"Parent ID: {user.parent_id}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(list_users()) 