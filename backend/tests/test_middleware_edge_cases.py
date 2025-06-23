"""
Test middleware edge cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from starlette.requests import Request

from backend.app.middleware.rate_limit import (
    limiter,
    RATE_LIMIT_RULES,
    get_rate_limit_key,
    authenticated_limiter,
    reset_limiter
)


class TestRateLimitMiddlewareEdgeCases:
    """Test rate limiting middleware edge cases."""
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_key_authenticated(self):
        """Test rate limit key for authenticated users."""
        # Mock request with user
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = Mock(id=123, username="testuser")
        
        key = get_rate_limit_key(request)
        assert key == "user:123"
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_key_anonymous(self):
        """Test rate limit key for anonymous users."""
        # Mock request without user
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.user = None
        request.client = Mock(host="192.168.1.100")
        request.headers = {}
        
        key = get_rate_limit_key(request)
        assert key == "192.168.1.100"
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_key_no_state_user(self):
        """Test rate limit key when state doesn't have user attribute."""
        # Mock request without state.user
        request = Mock(spec=Request)
        request.state = Mock(spec=[])  # Empty spec, no user attribute
        request.client = Mock(host="127.0.0.1")
        request.headers = {}
        
        key = get_rate_limit_key(request)
        assert key == "127.0.0.1"
    
    @pytest.mark.asyncio
    async def test_rate_limit_rules_structure(self):
        """Test that rate limit rules are properly structured."""
        assert "auth" in RATE_LIMIT_RULES
        assert "login" in RATE_LIMIT_RULES["auth"]
        assert "register" in RATE_LIMIT_RULES["auth"]
        
        assert "api" in RATE_LIMIT_RULES
        assert "default" in RATE_LIMIT_RULES["api"]
        assert "create" in RATE_LIMIT_RULES["api"]
        
        # Check format of limits
        login_limit = RATE_LIMIT_RULES["auth"]["login"]
        assert "per minute" in login_limit
    
    @pytest.mark.asyncio
    async def test_limiter_configuration(self):
        """Test that limiter is properly configured."""
        assert limiter is not None
        assert hasattr(limiter, 'limit')
        assert hasattr(limiter, 'shared_limit')
        
        # Check default limits
        assert limiter._default_limits is not None
        assert len(limiter._default_limits) > 0