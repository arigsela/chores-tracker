from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi.security import OAuth2PasswordRequestForm

from ....db.base import get_db
from ....repositories.user import UserRepository
from ....schemas.user import UserCreate, UserResponse, UserLogin, Token
from ....core.security.jwt import create_access_token

router = APIRouter()
user_repo = UserRepository()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
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