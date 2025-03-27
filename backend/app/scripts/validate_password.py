import asyncio
import sys
from app.db.base import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.core.security.password import verify_password

async def validate_user_password(username, password_to_try):
    """Validate a user's password without changing it."""
    async with AsyncSessionLocal() as session:
        # Find the user
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        
        if not user:
            print(f"User '{username}' not found in the database.")
            return False
        
        # Validate the password
        is_valid = verify_password(password_to_try, user.hashed_password)
        
        print(f"User information:")
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Is Parent: {user.is_parent}")
        print(f"Is Active: {user.is_active}")
        print(f"Password validation result: {'Valid' if is_valid else 'Invalid'}")
        
        return is_valid

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.scripts.validate_password <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    result = asyncio.run(validate_user_password(username, password))
    sys.exit(0 if result else 1) 