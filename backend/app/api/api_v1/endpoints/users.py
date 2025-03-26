from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
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

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    username: str = Form(...),
    password: str = Form(...),
    is_parent: str = Form(...),
    email: Optional[str] = Form(None),
    parent_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """Register a new user."""
    # Convert form data to the right types
    is_parent_bool = is_parent.lower() == "true"
    
    # If parent, email is required and must be valid
    if is_parent_bool:
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
    
    # Validate password length
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
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
        "username": username,
        "password": password,
        "is_parent": is_parent_bool,
        "parent_id": parent_id_int
    }
    
    # Add email if provided
    if email:
        user_data["email"] = email
    
    # Check if user with email already exists, if email provided
    if email:
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
    
    # Check if this is from a form (HTMX request)
    accept_header = authorization and "text/html" in authorization
    
    # If child account and from form, return HTML success message
    if not is_parent_bool:
        success_html = f"""
        <div class="bg-green-100 p-6 rounded-lg shadow-md border-2 border-green-300">
            <h2 class="text-2xl font-bold mb-4 text-green-700 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Success!
            </h2>
            <p class="text-green-700 mb-2">Child account for <span class="font-bold">{username}</span> has been created successfully.</p>
            <button 
                class="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                onclick="document.getElementById('main-content').innerHTML = '';">
                Close
            </button>
        </div>
        """
        return HTMLResponse(content=success_html, status_code=status.HTTP_201_CREATED)
    
    # Otherwise return the user data for API clients
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
    
    # If user is a parent, email is required
    if user_in.is_parent and not user_in.email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email is required for parent accounts"
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
        
    # Check if user already exists with the same email, if email provided
    if user_in.email:
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