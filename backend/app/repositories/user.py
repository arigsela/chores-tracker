from typing import Optional, Dict, Any, List
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models.user import User
from ..core.security.password import get_password_hash, verify_password

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """Get a user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()
    
    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> User:
        """Create a new user with hashed password."""
        db_obj = User(
            email=obj_in.get("email"),
            username=obj_in["username"],
            hashed_password=get_password_hash(obj_in["password"]),
            is_active=True,
            is_parent=obj_in["is_parent"],
            parent_id=obj_in.get("parent_id")
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def authenticate(self, db: AsyncSession, *, username: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        print(f"DEBUG [AUTH-1]: Authentication attempt for username: {username}")
        
        # Get user by direct SQL query to bypass any ORM caching
        query = text("SELECT id, username, hashed_password FROM users WHERE username = :username")
        result = await db.execute(query, {"username": username})
        user_row = result.fetchone()
        
        if not user_row:
            print(f"DEBUG [AUTH-2]: User not found with username '{username}' using direct SQL")
            return None
        
        user_id = user_row[0]
        db_username = user_row[1]
        hashed_password = user_row[2]
        
        print(f"DEBUG [AUTH-3]: Found user with direct SQL: ID={user_id}, username={db_username}")
        print(f"DEBUG [AUTH-4]: Password from DB hash (first 15 chars): {hashed_password[:15]}...")
        print(f"DEBUG [AUTH-5]: Provided password length: {len(password)}")
        
        # Get full user object using ORM
        user = await self.get(db, id=user_id)
        if not user:
            print(f"DEBUG [AUTH-6]: Failed to fetch full user object for ID={user_id}")
            return None
        
        # Log password details (exclude actual password for security)
        print(f"DEBUG [AUTH-7]: ORM user object: ID={user.id}, username={user.username}")
        
        # Verify password
        verification_result = verify_password(password, hashed_password)
        print(f"DEBUG [AUTH-8]: Password verification result: {verification_result}")
        
        if not verification_result:
            print(f"DEBUG [AUTH-9]: Password verification failed for user: {username}")
            return None
        
        print(f"DEBUG [AUTH-10]: Authentication successful for user: {username}")
        return user
    
    async def get_children(self, db: AsyncSession, *, parent_id: int) -> List[User]:
        """Get all children for a parent."""
        result = await db.execute(
            select(User).where(
                User.parent_id == parent_id,
                User.is_parent == False
            )
        )
        return result.scalars().all()
    
    async def reset_password(self, db: AsyncSession, *, user_id: int, new_password: str) -> Optional[User]:
        """Reset a user's password."""
        # Validate password length
        if len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters long")
        
        print(f"DEBUG: Resetting password for user_id={user_id}, password_length={len(new_password)}")
            
        # Hash the new password
        hashed_password = get_password_hash(new_password)
        print(f"DEBUG: Generated hashed password: {hashed_password[:10]}...")
        
        # Update the user's password
        updated_user = await self.update(db, id=user_id, obj_in={"hashed_password": hashed_password})
        
        # Verify the update was successful
        if updated_user:
            print(f"DEBUG: Password reset successful for user_id={user_id}, username={updated_user.username}")
            # Force a commit to ensure changes are persisted
            await db.commit()
            # Refresh the user from the database to verify the change
            await db.refresh(updated_user)
            print(f"DEBUG: Verified hashed_password in DB: {updated_user.hashed_password[:10]}...")
        else:
            print(f"DEBUG: Failed to update password for user_id={user_id}")
        
        return updated_user
    
    async def update_password(self, db: AsyncSession, *, user_id: int, new_password: str) -> Optional[User]:
        """Update a user's password."""
        # This is an alias for reset_password for consistency with the service layer
        return await self.reset_password(db, user_id=user_id, new_password=new_password)