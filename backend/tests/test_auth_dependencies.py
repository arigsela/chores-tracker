"""
Tests for authentication dependencies.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import get_current_user
from backend.app.models.user import User
from backend.app.core.security.jwt import create_access_token


class TestAuthDependencies:
    """Test authentication dependency functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(
        self,
        db_session: AsyncSession,
        test_parent_user: User
    ):
        """Test getting current user with valid token."""
        token = create_access_token(subject=test_parent_user.id)
        
        user = await get_current_user(token=token, db=db_session)
        
        assert user is not None
        assert user.id == test_parent_user.id
        assert user.username == test_parent_user.username
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        db_session: AsyncSession
    ):
        """Test getting current user with invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "invalid authentication credentials" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self,
        db_session: AsyncSession,
        test_parent_user: User
    ):
        """Test getting current user with expired token."""
        # Create token with negative expiration
        from datetime import datetime, timedelta
        from jose import jwt
        from backend.app.core.config import settings
        
        expire = datetime.utcnow() - timedelta(minutes=1)
        to_encode = {"exp": expire, "sub": str(test_parent_user.id)}
        expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=expired_token, db=db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(
        self,
        db_session: AsyncSession
    ):
        """Test getting current user with token for non-existent user."""
        # Create token for non-existent user ID
        token = create_access_token(subject=99999)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "user not found" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_sub_in_token(
        self,
        db_session: AsyncSession
    ):
        """Test token without subject claim."""
        from jose import jwt
        from backend.app.core.config import settings
        from datetime import datetime, timedelta
        
        # Create token without 'sub' claim
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode = {"exp": expire}  # Missing 'sub'
        bad_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        
        # This will raise a KeyError from verify_token when 'sub' is missing
        with pytest.raises((HTTPException, KeyError)):
            await get_current_user(token=bad_token, db=db_session)