from typing import Optional, Dict, Any, List
from sqlalchemy import select
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
        user = await self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
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