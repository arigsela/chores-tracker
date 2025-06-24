"""
Rate limiting middleware for API endpoints.

This module provides rate limiting functionality to prevent API abuse.
Different limits are applied based on endpoint sensitivity and authentication status.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

# Create limiter instance with default key function
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

# Define rate limit rules for different endpoint categories
RATE_LIMIT_RULES = {
    # Authentication endpoints - stricter limits
    "auth": {
        "login": "5 per minute",
        "register": "3 per minute",
        "token_refresh": "10 per minute",
    },
    # API endpoints - moderate limits
    "api": {
        "default": "100 per minute",
        "create": "30 per minute",
        "update": "50 per minute",
        "delete": "20 per minute",
    },
    # Static/UI endpoints - relaxed limits
    "ui": {
        "default": "200 per minute",
    }
}

def get_rate_limit_key(request: Request) -> str:
    """
    Generate a rate limit key based on user authentication status.
    
    Authenticated users get their own rate limit bucket based on user ID.
    Unauthenticated users share rate limit buckets based on IP address.
    """
    # Check if user is authenticated (has user attribute set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        # Use user ID for authenticated users
        return f"user:{request.state.user.id}"
    else:
        # Use IP address for unauthenticated users
        return get_remote_address(request)

# Create custom limiter for authenticated users
authenticated_limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["300 per minute"],  # Higher limit for authenticated users
    storage_uri="memory://",
)

def setup_rate_limiting(app):
    """
    Configure rate limiting for the FastAPI application.
    
    This function should be called during app initialization to set up
    rate limiting middleware and error handlers.
    """
    from ..core.config import settings
    
    # Skip rate limiting in test environment
    if settings.TESTING:
        logger.info("Rate limiting disabled for testing")
        return
    
    # Add rate limit exceeded error handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add SlowAPI middleware for request tracking
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info("Rate limiting configured successfully")

def reset_limiter():
    """Reset the rate limiter storage. Useful for testing."""
    # Reset the storage for both limiters
    from limits.storage.memory import MemoryStorage
    
    # Create new storage instances
    limiter._storage = MemoryStorage()
    authenticated_limiter._storage = MemoryStorage()

# Decorator functions for different endpoint types
def limit_auth_endpoint(limit: str = None):
    """Decorator for authentication endpoints with strict limits."""
    return limiter.limit(limit or RATE_LIMIT_RULES["auth"]["login"])

def limit_api_endpoint(limit: str = None):
    """Decorator for API endpoints with moderate limits."""
    return limiter.limit(limit or RATE_LIMIT_RULES["api"]["default"])

def limit_ui_endpoint(limit: str = None):
    """Decorator for UI endpoints with relaxed limits."""
    return limiter.limit(limit or RATE_LIMIT_RULES["ui"]["default"])

# Create no-op decorator for testing
def no_op_decorator(func):
    """No-operation decorator for when rate limiting is disabled."""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if first arg is Request and remove it
        from starlette.requests import Request
        if args and isinstance(args[0], Request):
            args = args[1:]
        return await func(*args, **kwargs)
    return wrapper

# Check if we're in testing mode
from ..core.config import settings

if settings.TESTING:
    # Use no-op decorators in testing mode
    limit_login = no_op_decorator
    limit_register = no_op_decorator
    limit_create = no_op_decorator
    limit_update = no_op_decorator
    limit_delete = no_op_decorator
    limit_api_endpoint_default = no_op_decorator
else:
    # Special decorators for specific operations
    limit_login = limiter.limit(RATE_LIMIT_RULES["auth"]["login"])
    limit_register = limiter.limit(RATE_LIMIT_RULES["auth"]["register"])
    limit_create = limiter.limit(RATE_LIMIT_RULES["api"]["create"])
    limit_update = limiter.limit(RATE_LIMIT_RULES["api"]["update"])
    limit_delete = limiter.limit(RATE_LIMIT_RULES["api"]["delete"])
    
    # For FastAPI compatibility
    limit_api_endpoint_default = limiter.limit(RATE_LIMIT_RULES["api"]["default"])