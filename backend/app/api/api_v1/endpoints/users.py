from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Header, Response, Request, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
import re
from sqlalchemy import text
from ....core.config import settings

from ....db.base import get_db
from ....schemas.user import UserCreate, UserResponse, Token, ChildAllowanceSummary
from ....core.security.jwt import create_access_token, verify_token
from ....dependencies.auth import get_current_user
from ....dependencies.services import UserServiceDep
from ....repositories.user import UserRepository
from ....models.user import User
from ....middleware.rate_limit import limit_login, limit_register, limit_api_endpoint_default

router = APIRouter()
# Convenience: get children for current parent (JSON)
@router.get(
    "/my-children",
    response_model=List[UserResponse],
    summary="Get children for current parent",
    description="""
    Get all child accounts for the authenticated parent.
    
    This is a convenience over `/users/children/{parent_id}` that infers the parent
    from the current authenticated user.
    """,
    tags=["users"],
    responses={
        200: {
            "description": "List of child accounts for current parent",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 2,
                            "username": "child_user",
                            "email": "child@example.com",
                            "is_parent": False,
                            "is_active": True,
                            "parent_id": 1
                        }
                    ]
                }
            }
        },
        403: {"description": "Only parents can list their children"}
    }
)
async def read_my_children(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceDep = None
):
    """
    Get children for the current authenticated parent.
    """
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can list their children"
        )
    # Prefer repository call to avoid issues if service injection differs
    children = await UserRepository().get_children(db, parent_id=current_user.id)
    return children


# Templates
# templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)  # No longer needed for REST API

# Simple email validation pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new parent or child user account.
    
    **Parent accounts** require:
    - Valid email address
    - Unique username
    - Strong password
    
    **Child accounts** require:
    - Unique username  
    - Password
    - Parent ID (must be authenticated as the parent)
    
    Rate limited to 3 requests per minute.
    """,
    response_description="User successfully created",
    responses={
        201: {
            "description": "User successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "is_parent": True,
                        "is_active": True,
                        "parent_id": None
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {"detail": "Email is required for parent accounts"}
                }
            }
        },
        400: {
            "description": "User already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Username already registered"}
                }
            }
        }
    }
)
@limit_register
async def register_user(
    request: Request,
    username: str = Form(..., description="Unique username for the account"),
    password: str = Form(..., description="Strong password (min 8 characters)"),
    is_parent: str = Form(..., description="'true' for parent, 'false' for child"),
    email: Optional[str] = Form(None, description="Email address (required for parents)"),
    parent_id: Optional[str] = Form(None, description="Parent's user ID (required for children)"),
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None, description="Bearer token if registering a child"),
    user_service: UserServiceDep = None
):
    """
    Register a new user account.
    
    This endpoint handles both parent and child registration:
    - Parents can self-register with email
    - Children must be registered by their parent (requires authentication)
    """
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
    
    # Return JSON response for REST API
    return user

# Keep the JSON-based endpoint for backward compatibility and API clients
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (JSON)",
    description="""
    Create a new user account using JSON payload.
    
    **Access**: Parents only
    
    **Use cases**:
    - Parents creating child accounts programmatically
    - API integrations
    
    For form-based registration, use the `/register` endpoint.
    
    Rate limited to 3 requests per minute.
    """,
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 3,
                        "username": "new_child",
                        "email": None,
                        "is_parent": False,
                        "is_active": True,
                        "parent_id": 1
                    }
                }
            }
        },
        403: {
            "description": "Only parents can create users"
        },
        422: {
            "description": "Validation error"
        }
    }
)
@limit_register
async def create_user(
    request: Request,
    user_in: UserCreate = Body(..., description="User creation data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceDep = None
):
    """
    Create a new user via JSON API.
    
    Only authenticated parents can create new users (typically their children).
    """
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

@router.post(
    "/login",
    response_model=Token,
    summary="Login to get access token",
    description="""
    Authenticate with username and password to receive a JWT access token.
    
    The token should be included in subsequent requests as:
    ```
    Authorization: Bearer <token>
    ```
    
    Rate limited to 5 requests per minute.
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials or inactive user",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid username or password"}
                }
            }
        },
        429: {
            "description": "Too many login attempts",
            "content": {
                "application/json": {
                    "example": {"detail": "Too Many Requests"}
                }
            }
        }
    },
    tags=["auth", "users"]
)
@limit_login
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    user_service: UserServiceDep = None
) -> dict:
    """
    Authenticate user and return JWT access token.
    
    Uses OAuth2 password flow with username and password.
    """
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

@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Get all users",
    description="""
    Retrieve a paginated list of all users in the system.
    
    **Access**: Authenticated users only
    
    **Note**: In production, this endpoint should be restricted to admin users only.
    Currently returns all users for development purposes.
    
    Rate limited to 100 requests per minute.
    """,
    responses={
        200: {
            "description": "List of users",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "username": "parent_user",
                            "email": "parent@example.com",
                            "is_parent": True,
                            "is_active": True,
                            "parent_id": None
                        },
                        {
                            "id": 2,
                            "username": "child_user",
                            "email": None,
                            "is_parent": False,
                            "is_active": True,
                            "parent_id": 1
                        }
                    ]
                }
            }
        }
    }
)
@limit_api_endpoint_default
async def read_users(
    request: Request,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    user_service: UserServiceDep = None
):
    """
    Get a list of all users with pagination support.
    """
    users = await user_service.get_multi(db, skip=skip, limit=limit)
    return users

@router.get(
    "/children/{parent_id}",
    response_model=List[UserResponse],
    summary="Get children for a parent",
    description="""
    Get all child accounts associated with a specific parent.
    
    **Access**: Currently open, should be restricted to the parent or admin users.
    
    **Returns**: List of child user accounts linked to the parent_id.
    """,
    responses={
        200: {
            "description": "List of child accounts",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 2,
                            "username": "alice_smith",
                            "email": None,
                            "is_parent": False,
                            "is_active": True,
                            "parent_id": 1
                        },
                        {
                            "id": 3,
                            "username": "bob_smith",
                            "email": None,
                            "is_parent": False,
                            "is_active": True,
                            "parent_id": 1
                        }
                    ]
                }
            }
        }
    }
)
async def read_children(
    parent_id: int = Path(..., description="The parent's user ID"),
    db: AsyncSession = Depends(get_db),
    user_service: UserServiceDep = None
):
    """
    Get all child accounts for a specific parent.
    """
    children = await user_service.repository.get_children(db, parent_id=parent_id)
    return children

@router.get(
    "/allowance-summary",
    response_model=List[ChildAllowanceSummary],
    summary="Get allowance summary for current parent",
    description="""
    Returns per-child allowance summary for the authenticated parent, including
    completed_chores, total_earned, total_adjustments, paid_out, and balance_due.
    """,
    tags=["users"],
    responses={
        200: {
            "description": "Per-child allowance summary",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 2,
                            "username": "child_user",
                            "completed_chores": 5,
                            "total_earned": 12.5,
                            "total_adjustments": -2.0,
                            "paid_out": 0.0,
                            "balance_due": 10.5
                        }
                    ]
                }
            }
        },
        403: {"description": "Only parents can access allowance summary"}
    }
)
async def read_parent_allowance_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access allowance summary",
        )

    # Reuse repository logic already used by HTML route in main.py
    from ....repositories.user import UserRepository
    from ....repositories.chore import ChoreRepository
    from ....repositories.reward_adjustment import RewardAdjustmentRepository

    user_repo = UserRepository()
    chore_repo = ChoreRepository()
    adjustment_repo = RewardAdjustmentRepository()

    children = await user_repo.get_children(db, parent_id=current_user.id)

    # Helper function to get final reward amount (matches frontend logic)
    def get_final_reward_amount(chore):
        # For approved chores, prioritize approval_reward field
        if chore.approval_reward is not None:
            return chore.approval_reward
        # Fallback to reward field (legacy and fixed rewards)
        return chore.reward or 0

    summary: List[ChildAllowanceSummary] = []
    for child in children:
        chores = await chore_repo.get_by_assignee(db, assignee_id=child.id)
        completed_chores = len([c for c in chores if c.is_completed and c.is_approved])
        total_earned = sum(get_final_reward_amount(c) for c in chores if c.is_completed and c.is_approved)
        total_adjustments = float(
            await adjustment_repo.calculate_total_adjustments(db, child_id=child.id)
        )
        paid_out = 0.0
        balance_due = total_earned + total_adjustments - paid_out

        summary.append(
            ChildAllowanceSummary(
                id=child.id,
                username=child.username,
                completed_chores=completed_chores,
                total_earned=float(total_earned),
                total_adjustments=float(total_adjustments),
                paid_out=float(paid_out),
                balance_due=float(balance_due),
            )
        )

    return summary

@router.post(
    "/children/{child_id}/reset-password",
    response_model=UserResponse,
    summary="Reset child's password",
    description="""
    Reset the password for a child account.
    
    **Access**: Parents only (must be the child's parent)
    
    **Security**:
    - Parent must be authenticated
    - Child must belong to the parent
    - New password must meet minimum requirements
    
    This endpoint is for JSON API clients. For HTMX/form submissions,
    use the `/html/children/{child_id}/reset-password` endpoint.
    """,
    responses={
        200: {
            "description": "Password reset successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "username": "child_user",
                        "is_parent": False,
                        "parent_id": 1,
                        "is_active": True
                    }
                }
            }
        },
        403: {
            "description": "Not authorized to reset this child's password"
        },
        404: {
            "description": "Child not found"
        },
        422: {
            "description": "Password does not meet requirements"
        }
    }
)
async def reset_child_password(
    child_id: int = Path(..., description="The child's user ID"),
    new_password: str = Body(..., description="New password (min 4 characters)", min_length=4),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_service: UserServiceDep = None
):
    """
    Reset a child's password.
    
    Only the child's parent can reset their password.
    """
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

@router.post("/html/children/{child_id}/reset-password")
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
        
        # Return success JSON
        print(f"DEBUG [33]: Returning success JSON")
        return JSONResponse(
            content={
                "success": True,
                "message": f"Password reset successfully for user {updated_child.username}",
                "username": updated_child.username
            },
            status_code=status.HTTP_200_OK
        )
    except ValueError as e:
        print(f"DEBUG [ERROR]: Password reset failed with ValueError: {str(e)}")
        # Return error JSON
        return JSONResponse(
            content={
                "success": False,
                "error": str(e)
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception as e:
        print(f"DEBUG [ERROR]: Unexpected error during password reset: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error JSON
        return JSONResponse(
            content={
                "success": False,
                "error": f"An unexpected error occurred: {str(e)}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )