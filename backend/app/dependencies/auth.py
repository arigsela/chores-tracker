from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..repositories.user import UserRepository
from ..core.security.jwt import verify_token
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login", auto_error=False)
user_repo = UserRepository()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_repo.get(db, id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get the current authenticated user if token is provided, otherwise return None."""
    if not token:
        return None
    
    user_id = verify_token(token)
    if not user_id:
        return None
    
    user = await user_repo.get(db, id=int(user_id))
    if not user or not user.is_active:
        return None
    
    return user