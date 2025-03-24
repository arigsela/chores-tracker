from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
import re

from ....db.base import get_db
from ....repositories.user import UserRepository
from ....schemas.user import UserCreate, UserResponse, UserLogin, Token
from ....core.security.jwt import create_access_token, verify_token
from ....dependencies.auth import get_current_user, oauth2_scheme

router = APIRouter()
user_repo = UserRepository()

# Simple email validation pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    is_parent: str = Form(...),
    parent_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Register a new user."""
    # Validate email with simple regex
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format"
        )
    
    # Validate password length
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    # Convert form data to the right types
    is_parent_bool = is_parent.lower() == "true"
    
    try:
        parent_id_int = int(parent_id) if parent_id else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Parent ID must be a valid integer"
        )
    
    # If not a parent, parent_id is required - get it from the current user if not provided
    if not is_parent_bool and not parent_id_int:
        # Try to get the current user from the authorization header
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            try:
                user_id = verify_token(token)
                if user_id:
                    # Get user from database
                    current_user = await user_repo.get(db, id=int(user_id))
                    if current_user and current_user.is_parent:
                        parent_id_int = current_user.id
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Parent ID is required for child accounts"
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Parent ID is required for child accounts"
                    )
            except Exception:
                # Failed to get user from token
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Parent ID is required for child accounts"
                )
        else:
            # No authorization header
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Parent ID is required for child accounts"
            )
    
    # Create user data object
    user_data = {
        "email": email,
        "username": username,
        "password": password,
        "is_parent": is_parent_bool,
        "parent_id": parent_id_int
    }
    
    # Check if user already exists
    db_user = await user_repo.get_by_email(db, email=email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    db_user = await user_repo.get_by_username(db, username=username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = await user_repo.create(db, obj_in=user_data)
    return user

# Keep the JSON-based endpoint for backward compatibility and API clients
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user (JSON endpoint)."""
    # Check if current user is a parent (only parents can create users)
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can create new users"
        )
    
    # Validate password length
    if len(user_in.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    # If not a parent, parent_id is required - set from current user if not provided
    if not user_in.is_parent and not user_in.parent_id:
        # Use the current user's ID as the parent_id
        user_in.parent_id = current_user.id
    
    # Validate parent_id exists if provided
    if user_in.parent_id:
        parent = await user_repo.get(db, id=user_in.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent user not found"
            )
        
    # Check if user already exists
    db_user = await user_repo.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    db_user = await user_repo.get_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = await user_repo.create(db, obj_in=user_in.dict())
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login a user."""
    user = await user_repo.authenticate(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive"
        )
    
    # Create access token
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """Get all users."""
    users = await user_repo.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/children/{parent_id}", response_model=List[UserResponse])
async def read_children(
    parent_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Get all children for a parent."""
    children = await user_repo.get_children(db, parent_id=parent_id)
    return children