"""Authentication endpoints v2 - JSON-only responses."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ....db.base import get_db
from ....schemas.user import Token
from ....schemas.api_response import ApiResponse, ErrorResponse
from ....dependencies.services import UserServiceDep
from ....core.security.jwt import create_access_token
from ....middleware.rate_limit import limit_login

router = APIRouter()


@router.post(
    "/login",
    response_model=ApiResponse[Token],
    summary="Login to get access token",
    description="""
    Authenticate with username and password to receive a JWT access token.
    
    Returns a standardized JSON response with the token in the data field.
    
    Rate limited to 5 requests per minute.
    """,
    responses={
        200: {
            "description": "Login successful",
            "model": ApiResponse[Token]
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse
        },
        429: {
            "description": "Too many login attempts",
            "model": ErrorResponse
        }
    }
)
@limit_login
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_service: UserServiceDep
) -> ApiResponse[Token]:
    """
    Authenticate user and return JWT access token.
    
    Uses OAuth2 password flow with username and password.
    Returns standardized API response.
    """
    try:
        # Use service to authenticate
        user = await user_service.authenticate(
            db=db,
            username=form_data.username,
            password=form_data.password
        )
        
        if not user.is_active:
            return ApiResponse(
                success=False,
                error="User account is inactive",
                data=None
            )
        
        # Create access token
        access_token = create_access_token(subject=str(user.id))
        
        return ApiResponse(
            success=True,
            data=Token(access_token=access_token, token_type="bearer"),
            error=None
        )
        
    except HTTPException as e:
        return ApiResponse(
            success=False,
            error=e.detail,
            data=None
        )
    except Exception as e:
        import traceback
        print(f"Login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return ApiResponse(
            success=False,
            error=f"Authentication failed: {str(e)}",
            data=None
        )