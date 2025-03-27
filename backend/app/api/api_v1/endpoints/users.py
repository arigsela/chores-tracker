from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Header, Response, Request
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
from ....core.security.password import get_password_hash
from sqlalchemy import text

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
    # Log the login attempt
    print(f"Login attempt for username: {form_data.username}")
    
    try:
        # Get user by username for debugging
        user_by_username = await user_repo.get_by_username(db, username=form_data.username)
        if not user_by_username:
            print(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Attempt authentication
        user = await user_repo.authenticate(db, username=form_data.username, password=form_data.password)
        if not user:
            print(f"Authentication failed for user: {form_data.username} (password mismatch)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
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

@router.post("/children/{child_id}/reset-password", response_model=UserResponse)
async def reset_child_password(
    child_id: int,
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Reset a child's password (JSON endpoint)."""
    # Ensure the current user is a parent
    if not current_user.is_parent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can reset passwords"
        )
    
    # Get the child user
    child = await user_repo.get(db, id=child_id)
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
    
    # Ensure the child belongs to the current parent
    if child.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reset passwords for your own children"
        )
    
    try:
        # Check minimum password length
        if len(new_password) < 4:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 4 characters long"
            )
        
        # Generate a new bcrypt hash directly
        import bcrypt
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Direct SQL update like in our working script
        query = text("UPDATE users SET hashed_password = :hashed_password WHERE id = :user_id")
        await db.execute(query, {"hashed_password": hashed_password, "user_id": child_id})
        await db.commit()
        
        # Get the updated user to return
        updated_child = await user_repo.get(db, id=child_id)
        return updated_child
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
    current_user: dict = Depends(get_current_user)
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
    child = await user_repo.get(db, id=child_id)
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
        
        # Generate a new bcrypt hash directly
        import bcrypt
        print(f"DEBUG [16]: Encoding password")
        password_bytes = new_password.encode('utf-8')
        print(f"DEBUG [17]: Generating salt")
        salt = bcrypt.gensalt(rounds=12)
        print(f"DEBUG [18]: Hashing password")
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        print(f"DEBUG [19]: Generated new password hash: {hashed_password[:15]}...")
        
        try:
            # Direct SQL update like in our working script
            print(f"DEBUG [20]: Preparing SQL query to update password")
            query = text("UPDATE users SET hashed_password = :hashed_password WHERE id = :user_id")
            print(f"DEBUG [21]: Executing SQL update for user_id={child_id}")
            await db.execute(query, {"hashed_password": hashed_password, "user_id": child_id})
            print(f"DEBUG [22]: Committing transaction")
            await db.commit()
            print(f"DEBUG [23]: Transaction committed")
        except Exception as sql_error:
            print(f"DEBUG [ERROR]: SQL update failed: {str(sql_error)}")
            raise
        
        try:
            # Verify the update worked
            print(f"DEBUG [24]: Verifying password update")
            verify_query = text("SELECT hashed_password FROM users WHERE id = :user_id")
            result = await db.execute(verify_query, {"user_id": child_id})
            updated_user = result.fetchone()
            
            if updated_user:
                print(f"DEBUG [25]: Found user after update, stored hash: {updated_user[0][:15]}...")
                if updated_user[0] == hashed_password:
                    print(f"DEBUG [26]: SUCCESS: Password hash matches! Update successful for {child.username}")
                else:
                    print(f"DEBUG [27]: WARNING: Password hash mismatch after update for {child.username}")
                    print(f"DEBUG [28]: Expected: {hashed_password[:15]}...")
                    print(f"DEBUG [29]: Found in DB: {updated_user[0][:15]}...")
            else:
                print(f"DEBUG [30]: ERROR: Could not find user after update")
        except Exception as verify_error:
            print(f"DEBUG [ERROR]: Verification query failed: {str(verify_error)}")
        
        # For database troubleshooting
        try:
            # Get engine details
            from sqlalchemy import inspect
            engine = db.get_bind()
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            print(f"DEBUG [31]: Database contains tables: {table_names}")
            
            # Dump all users and their password hashes
            dump_query = text("SELECT id, username, hashed_password FROM users")
            dump_result = await db.execute(dump_query)
            dump_rows = dump_result.fetchall()
            for row in dump_rows:
                print(f"DEBUG [32]: USER #{row[0]} {row[1]}: hash={row[2][:15]}...")
        except Exception as db_error:
            print(f"DEBUG [ERROR]: Database inspection failed: {str(db_error)}")
        
        # Return success HTML
        print(f"DEBUG [33]: Returning success HTML")
        success_html = f"""
        <div class="bg-white p-6 rounded-lg shadow-md text-center">
            <h2 class="text-2xl font-bold text-green-600 mb-4">
                Password Reset Successful
            </h2>
            <p class="text-green-700 mb-2">Password for <span class="font-bold">{child.username}</span> has been reset successfully.</p>
            <button 
                class="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                onclick="localStorage.removeItem('token'); window.location.href = '/pages/login';">
                Log Out to Test New Password
            </button>
        </div>
        """
        return HTMLResponse(content=success_html, status_code=status.HTTP_200_OK)
    except ValueError as e:
        print(f"DEBUG [ERROR]: Password reset failed with ValueError: {str(e)}")
        # Return error HTML
        error_html = f"""
        <div class="bg-white p-6 rounded-lg shadow-md text-center">
            <h2 class="text-2xl font-bold text-red-600 mb-4">
                Password Reset Failed
            </h2>
            <p class="text-red-700 mb-2">{str(e)}</p>
            <button 
                class="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                onclick="document.getElementById('main-content').innerHTML = '';">
                Close
            </button>
        </div>
        """
        return HTMLResponse(content=error_html, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        print(f"DEBUG [ERROR]: Unexpected error during password reset: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error HTML
        error_html = f"""
        <div class="bg-white p-6 rounded-lg shadow-md text-center">
            <h2 class="text-2xl font-bold text-red-600 mb-4">
                Password Reset Failed
            </h2>
            <p class="text-red-700 mb-2">An unexpected error occurred: {str(e)}</p>
            <button 
                class="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                onclick="document.getElementById('main-content').innerHTML = '';">
                Close
            </button>
        </div>
        """
        return HTMLResponse(content=error_html, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)