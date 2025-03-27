import asyncio
import sys
from backend.app.db.base import AsyncSessionLocal
from backend.app.models.user import User
from sqlalchemy import update
from backend.app.core.security.password import get_password_hash

async def reset_user_password(username, new_password):
    """Reset a user's password."""
    async with AsyncSessionLocal() as session:
        # Find the user
        result = await session.execute(update(User).where(User.username == username).values(
            hashed_password=get_password_hash(new_password)
        ).returning(User))
        
        user = result.scalars().first()
        
        if not user:
            print(f"User '{username}' not found in the database.")
            return False
        
        await session.commit()
        
        print(f"Password for user '{username}' (ID: {user.id}) has been reset.")
        print(f"New password: {new_password}")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m backend.app.scripts.reset_password <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    if len(new_password) < 4:
        print("Password must be at least 4 characters long")
        sys.exit(1)
    
    result = asyncio.run(reset_user_password(username, new_password))
    sys.exit(0 if result else 1) 