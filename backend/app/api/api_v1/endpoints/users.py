from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Header, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import re
from sqlalchemy import text
from ....core.config import settings

from ....db.base import get_db
from ....schemas.user import UserCreate, UserResponse, Token
from ....core.security.jwt import create_access_token, verify_token
from ....dependencies.auth import get_current_user
from ....dependencies.services import UserServiceDep
from ....models.user import User
from ....middleware.rate_limit import limit_login, limit_register, limit_api_endpoint_default

router = APIRouter()

# Templates
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

# Simple email validation pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limit_register
async def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_parent: str = Form(...),
    email: Optional[str] = Form(None),
    parent_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    user_service: UserServiceDep = None
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
                    current_user = await user_service.get_current_user(db, user_id=int(user_id))
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
    
    # Use service to register user
    try:
        user = await user_service.register_user(
            db=db,
            username=user_data["username"],
            password=user_data["password"],
            is_parent=user_data["is_parent"],
            parent_id=user_data.get("parent_id"),
            email=user_data.get("email")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check if this is from a form (HTMX request)
    # accept_header = authorization and "text/html" in authorization
    
    # If child account and from form, return HTML success message
    if not is_parent_bool:
        return templates.TemplateResponse(
            "components/child_account_created.html",
            {"request": Request(scope={"type": "http", "headers": []}, receive=None), "username": username},
            status_code=status.HTTP_201_CREATED
        )
    
    # Otherwise return the user data for API clients
    return user

# Keep the JSON-based endpoint for backward compatibility and API clients
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limit_register
async def create_user(
    request: Request,
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceDep = None
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
    
    # Use service to register user
    try:
        user = await user_service.register_user(
            db=db,
            username=user_in.username,
            password=user_in.password,
            is_parent=user_in.is_parent,
            parent_id=user_in.parent_id,
            email=user_in.email
        )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
@limit_login
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    user_service: UserServiceDep = None
) -> dict:
    """Login a user."""
    # Log the login attempt
    print(f"Login attempt for username: {form_data.username}")
    
    try:
        # Use service to authenticate
        user = await user_service.authenticate(
            db=db,
            username=form_data.username,
            password=form_data.password
        )
        
        if not user.is_active:
            print(f"User is inactive: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive"
            )
        
        # Create access token
        token = create_access_token(subject=user.id)
        print(f"Login successful for user: {form_data.username} (ID: {user.id})")
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        print(f"Exception during login: {str(e)}")
        raise

@router.get("/", response_model=List[UserResponse])
@limit_api_endpoint_default
async def read_users(
    request: Request,
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    user_service: UserServiceDep = None
):
    """Get all users."""
    users = await user_service.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/children/{parent_id}", response_model=List[UserResponse])
async def read_children(
    parent_id: int, 
    db: AsyncSession = Depends(get_db),
    user_service: UserServiceDep = None
):
    """Get all children for a parent."""
    children = await user_service.repository.get_children(db, parent_id=parent_id)
    return children

@router.post("/children/{child_id}/reset-password", response_model=UserResponse)
async def reset_child_password(
    child_id: int,
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceDep = None
):
    """Reset a child's password (JSON endpoint)."""
    # Ensure the current user is a parent
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can reset passwords"
        )
    
    # Use service to reset password
    try:
        updated_child = await user_service.reset_child_password(
            db=db,
            parent_id=current_user.id,
            child_id=child_id,
            new_password=new_password
        )
        return updated_child
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting password: {str(e)}"
        )

@router.post("/html/children/{child_id}/reset-password", response_class=HTMLResponse)
async def reset_child_password_html(
    request: Request,
    child_id: int,
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceDep = None
):
    """Reset a child's password with HTML response."""
    # Debug info for the request
    print(f"DEBUG [REQ-1]: Received password reset request for child_id={child_id}")
    print(f"DEBUG [REQ-2]: Request method: {request.method}")
    print(f"DEBUG [REQ-3]: Request headers: {dict(request.headers)}")
    print(f"DEBUG [REQ-4]: new_password length: {len(new_password)}, first/last chars: {new_password[:1]}...{new_password[-1:] if len(new_password) > 0 else ''}")
    print(f"DEBUG [REQ-5]: Current user ID: {current_user.id}, username: {current_user.username}")
    
    # Log receipt of all form fields 
    form_data = await request.form()
    print(f"DEBUG [REQ-6]: Form data keys: {list(form_data.keys())}")
    
    # Ensure the current user is a parent
    if not current_user.is_parent:
        print(f"DEBUG [4]: User {current_user.username} is not a parent")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can reset passwords"
        )
    
    print(f"DEBUG [5]: User {current_user.username} is a parent, continuing...")
    
    # Get the child user
    child = await user_service.get(db, id=child_id)
    if not child:
        print(f"DEBUG [6]: Child with ID {child_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )
    
    print(f"DEBUG [7]: Found child: {child.username} (ID: {child.id})")
    
    # Ensure the child is actually a child (not a parent)
    if child.is_parent:
        print(f"DEBUG [8]: User {child.username} is a parent, not a child")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reset password for a parent account"
        )
    
    print(f"DEBUG [9]: Confirmed {child.username} is a child account")
    
    # Ensure the child belongs to the current parent
    if child.parent_id != current_user.id:
        print(f"DEBUG [10]: Child {child.username} does not belong to parent {current_user.username}")
        print(f"DEBUG [11]: Child's parent_id={child.parent_id}, current user ID={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reset passwords for your own children"
        )
    
    print(f"DEBUG [12]: Confirmed child {child.username} belongs to parent {current_user.username}")
    
    try:
        # Check minimum password length
        if len(new_password) < 4:
            print(f"DEBUG [13]: Password too short: {len(new_password)} chars")
            raise ValueError("Password must be at least 4 characters long")
        
        print(f"DEBUG [14]: Password length OK: {len(new_password)} chars")
        print(f"DEBUG [15]: Resetting password for child {child.username} (ID: {child.id})")
        
        # Use service to handle password reset
        print(f"DEBUG [16-23]: Using service to handle password reset")
        updated_child = await user_service.reset_child_password(
            db=db,
            parent_id=current_user.id,
            child_id=child_id,
            new_password=new_password
        )
        print(f"DEBUG [24]: Password reset completed by service")
        
        # Verification is now handled by the service
        print(f"DEBUG [25-30]: Password update verification completed by service")
        
        # Database troubleshooting is now handled at the service level
        print(f"DEBUG [31-32]: Service completed all database operations")
        
        # Return success HTML
        print(f"DEBUG [33]: Returning success HTML")
        return templates.TemplateResponse(
            "components/password_reset_dialog.html",
            {
                "request": Request(scope={"type": "http", "headers": []}, receive=None),
                "success": True,
                "username": updated_child.username
            },
            status_code=status.HTTP_200_OK
        )
    except ValueError as e:
        print(f"DEBUG [ERROR]: Password reset failed with ValueError: {str(e)}")
        # Return error HTML
        return templates.TemplateResponse(
            "components/password_reset_dialog.html",
            {
                "request": Request(scope={"type": "http", "headers": []}, receive=None),
                "success": False,
                "error_message": str(e)
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        print(f"DEBUG [ERROR]: Unexpected error during password reset: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error HTML
        return templates.TemplateResponse(
            "components/password_reset_dialog.html",
            {
                "request": Request(scope={"type": "http", "headers": []}, receive=None),
                "success": False,
                "error_message": f"An unexpected error occurred: {str(e)}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )