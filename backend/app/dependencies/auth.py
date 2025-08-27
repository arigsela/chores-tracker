from typing import Optional, Dict, Any, NamedTuple
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..repositories.user import UserRepository
from ..repositories.family import FamilyRepository
from ..core.security.jwt import verify_token
from ..models.user import User
from ..models.family import Family


class UserWithFamily(NamedTuple):
    """User with loaded family context for efficient API operations."""
    user: User
    family: Optional[Family]
    family_role: str  # "parent", "child", or "no_family"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
user_repo = UserRepository()
family_repo = FamilyRepository()

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


async def get_current_user_with_family(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserWithFamily:
    """Get the current authenticated user with family context loaded."""
    # First get the user using existing logic
    user = await get_current_user(token, db)
    
    # Load family context if user has a family
    family = None
    family_role = "no_family"
    
    if user.family_id:
        family = await family_repo.get(db, id=user.family_id)
        family_role = "parent" if user.is_parent else "child"
    
    return UserWithFamily(user=user, family=family, family_role=family_role)


async def get_current_parent(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current authenticated user, ensuring they are a parent."""
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires parent privileges"
        )
    return current_user


async def get_current_parent_with_family(
    user_with_family: UserWithFamily = Depends(get_current_user_with_family)
) -> UserWithFamily:
    """Get the current authenticated parent with family context."""
    if not user_with_family.user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires parent privileges"
        )
    return user_with_family


async def require_family_membership(
    user_with_family: UserWithFamily = Depends(get_current_user_with_family)
) -> UserWithFamily:
    """Ensure the current user belongs to a family."""
    if not user_with_family.family:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires family membership. Please create or join a family first."
        )
    return user_with_family


def validate_family_access(family_id: int):
    """Create a dependency that validates user has access to a specific family."""
    async def _validate_access(
        user_with_family: UserWithFamily = Depends(get_current_user_with_family),
        db: AsyncSession = Depends(get_db)
    ) -> UserWithFamily:
        """Validate user has access to the specified family."""
        if not user_with_family.family:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of any family"
            )
        
        if user_with_family.family.id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this family"
            )
        
        return user_with_family
    
    return _validate_access


def validate_user_access(target_user_id: int):
    """Create a dependency that validates user can access another user's data."""
    async def _validate_user_access(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Validate user has access to target user's data."""
        # Same user can always access their own data
        if current_user.id == target_user_id:
            return current_user
        
        # Get target user
        target_user = await user_repo.get(db, id=target_user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        
        # Parents can access their direct children (legacy mode)
        if current_user.is_parent and target_user.parent_id == current_user.id:
            return current_user
        
        # Family-based access
        if current_user.family_id and current_user.family_id == target_user.family_id:
            # Parents can access any family member's data
            if current_user.is_parent:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this user's data"
        )
    
    return _validate_user_access