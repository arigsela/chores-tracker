"""
User service with business logic for user operations.
"""
import re
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService
from ..models.user import User
from ..models.chore import Chore
from ..repositories.user import UserRepository
from ..schemas.user import UserCreate
from ..core.security.jwt import create_access_token, verify_token
from ..core.security.password import verify_password
from ..core.unit_of_work import UnitOfWork


# Email validation pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserService(BaseService[User, UserRepository]):
    """Service for user-related business logic."""
    
    def __init__(self):
        """Initialize user service."""
        super().__init__(UserRepository())
    
    async def register_user(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
        is_parent: bool,
        email: Optional[str] = None,
        parent_id: Optional[int] = None,
        current_user_id: Optional[int] = None
    ) -> User:
        """
        Register a new user with validation.
        
        Business rules:
        - Parents must have a valid email
        - Children must have a parent_id
        - Username must be unique
        - Email must be unique (if provided)
        - Password must be at least 8 characters
        """
        # Validate password length
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 8 characters long"
            )
        
        # Validate parent requirements
        if is_parent:
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Email is required for parent accounts"
                )
            if not EMAIL_PATTERN.match(email):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid email format"
                )
        
        # Validate child requirements
        if not is_parent:
            # If no parent_id provided, use current user if they're a parent
            if not parent_id and current_user_id:
                current_user = await self.get(db, id=current_user_id)
                if current_user and current_user.is_parent:
                    parent_id = current_user.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Parent ID is required for child accounts"
                    )
            elif not parent_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Parent ID is required for child accounts"
                )
            
            # Validate parent exists
            if parent_id:
                parent = await self.get(db, id=parent_id)
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent user not found"
                    )
        
        # Check if username already exists
        existing_user = await self.repository.get_by_username(db, username=username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Check if email already exists (if provided)
        if email:
            existing_email = await self.repository.get_by_email(db, email=email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Create user data
        user_data = {
            "username": username,
            "password": password,
            "is_parent": is_parent,
            "parent_id": parent_id
        }
        if email:
            user_data["email"] = email
        
        # Create user
        return await self.repository.create(db, obj_in=user_data)
    
    async def authenticate(
        self, db: AsyncSession, *, username: str, password: str
    ) -> tuple[User, str]:
        """
        Authenticate user and return user with access token.
        
        Raises HTTPException if authentication fails.
        """
        # Get user by username
        user = await self.repository.get_by_username(db, username=username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive"
            )
        
        return user
    
    async def get_current_user(
        self, db: AsyncSession, *, user_id: int = None, token: str = None
    ) -> User:
        """
        Get current user from token or user_id.
        
        Raises HTTPException if token is invalid or user not found.
        """
        # If user_id is provided directly, use it
        if user_id is None and token:
            # Verify token
            user_id = verify_token(token)
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user identification provided"
            )
        
        # Get user
        user = await self.get(db, id=int(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    async def get_children(
        self, db: AsyncSession, *, parent_id: int
    ) -> list[User]:
        """Get all children for a parent."""
        return await self.repository.get_children(db, parent_id=parent_id)
    
    async def get_children_for_parent(
        self, db: AsyncSession, *, parent_id: int
    ) -> list[User]:
        """Get all children for a parent - alias for get_children."""
        return await self.get_children(db, parent_id=parent_id)
    
    async def count(self, db: AsyncSession) -> int:
        """Get total count of users."""
        return await self.repository.count(db)
    
    async def reset_child_password(
        self,
        db: AsyncSession,
        *,
        parent_id: int,
        child_id: int,
        new_password: str
    ) -> User:
        """
        Reset a child's password.
        
        Business rules:
        - Only parents can reset passwords
        - Can only reset password for own children
        - Password must be at least 4 characters
        """
        # Get the child user
        child = await self.get(db, id=child_id)
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Ensure the child is actually a child (not a parent)
        if child.is_parent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot reset password for a parent account"
            )
        
        # Ensure the child belongs to the parent
        if child.parent_id != parent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reset passwords for your own children"
            )
        
        # Validate password length
        if len(new_password) < 4:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 4 characters long"
            )
        
        # Update password using repository method
        updated_user = await self.repository.update_password(
            db, user_id=child_id, new_password=new_password
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return updated_user
    
    async def register_family(
        self,
        uow: UnitOfWork,
        *,
        parent_data: Dict[str, Any],
        children_data: List[Dict[str, Any]] = None,
        initial_chores: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a complete family with parent, children, and initial chores.
        
        This is a transactional operation - if any part fails, everything is rolled back.
        
        Args:
            uow: Unit of Work for transaction management
            parent_data: Parent user data (username, password, email)
            children_data: List of child user data (username, password)
            initial_chores: List of chores to create and assign
            
        Returns:
            Dictionary with created parent, children, and chores
            
        Example:
            async with UnitOfWork() as uow:
                result = await user_service.register_family(
                    uow,
                    parent_data={"username": "mom", "password": "pass123", "email": "mom@example.com"},
                    children_data=[
                        {"username": "child1", "password": "pass123"},
                        {"username": "child2", "password": "pass123"}
                    ],
                    initial_chores=[
                        {"title": "Clean room", "assignee": "child1", "reward": 5.0},
                        {"title": "Take out trash", "assignee": "child2", "reward": 3.0}
                    ]
                )
                await uow.commit()
        """
        try:
            # Create parent account
            parent = await self.register_user(
                uow.session,
                username=parent_data["username"],
                password=parent_data["password"],
                email=parent_data["email"],
                is_parent=True
            )
            
            created_children = []
            created_chores = []
            
            # Create children accounts if provided
            if children_data:
                child_username_to_id = {}
                
                for child_data in children_data:
                    child = await self.register_user(
                        uow.session,
                        username=child_data["username"],
                        password=child_data["password"],
                        is_parent=False,
                        parent_id=parent.id
                    )
                    created_children.append(child)
                    child_username_to_id[child.username] = child.id
                
                # Create initial chores if provided
                if initial_chores:
                    for chore_data in initial_chores:
                        # Find assignee ID if username provided
                        assignee_id = None
                        if "assignee" in chore_data:
                            assignee_id = child_username_to_id.get(chore_data["assignee"])
                            if not assignee_id:
                                raise ValueError(f"Unknown assignee: {chore_data['assignee']}")
                        
                        # Create chore
                        chore = await uow.chores.create(
                            uow.session,
                            obj_in={
                                "title": chore_data["title"],
                                "description": chore_data.get("description", ""),
                                "reward": chore_data["reward"],
                                "is_range_reward": False,
                                "cooldown_days": chore_data.get("cooldown_days", 0),
                                "is_recurring": chore_data.get("is_recurring", False),
                                "creator_id": parent.id,
                                "assignee_id": assignee_id,
                                "is_completed": False,
                                "is_approved": False,
                                "is_disabled": False
                            }
                        )
                        created_chores.append(chore)
            
            return {
                "parent": parent,
                "children": created_children,
                "chores": created_chores
            }
            
        except Exception as e:
            # Transaction will be rolled back automatically by UnitOfWork
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to register family: {str(e)}"
            )