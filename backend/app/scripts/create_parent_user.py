#!/usr/bin/env python3
"""Script to create a parent user."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from backend.app.db.base import AsyncSessionLocal
from backend.app.models.user import User
from backend.app.core.security.password import get_password_hash


async def create_parent_user(username: str, password: str, email: str, full_name: str):
    """Create a parent user."""
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User '{username}' already exists")
            return
        
        # Create new parent user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_parent=True,
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"Successfully created parent user:")
        print(f"  Username: {user.username}")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Is Parent: {user.is_parent}")


if __name__ == "__main__":
    # Default values
    username = "testparent2"
    password = "parentpass123"
    email = "testparent2@example.com"
    full_name = "Test Parent Two"
    
    # Run the async function
    asyncio.run(create_parent_user(username, password, email, full_name))