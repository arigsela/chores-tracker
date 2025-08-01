"""
Request validation middleware for the chores tracker application.

Provides additional validation beyond FastAPI's built-in validation:
- Content-type validation
- Request size limits
- Malformed JSON handling
- Input sanitization
"""
import json
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Configuration
MAX_REQUEST_SIZE = 1 * 1024 * 1024  # 1 MB
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/x-www-form-urlencoded",
    "multipart/form-data"
}


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating incoming requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and validate it."""
        
        # Skip validation for GET, HEAD, OPTIONS requests
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Skip validation for non-API endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        
        try:
            # 1. Validate content-type for requests with body
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "").lower()
                
                # Skip validation if no content-type is provided (common in tests)
                if not content_type:
                    # Allow missing content-type for backwards compatibility
                    pass
                else:
                    # Extract base content type (ignore charset, boundary, etc.)
                    base_content_type = content_type.split(";")[0].strip()
                    
                    # Special handling for form submissions (HTMX)
                    if request.url.path.endswith("/html") or "hx-request" in request.headers:
                        # Allow form data for HTML endpoints
                        pass
                    elif base_content_type not in ALLOWED_CONTENT_TYPES:
                        logger.warning(
                            f"Invalid content-type: {content_type} for {request.url.path}"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            content={
                                "error": {
                                    "code": "UNSUPPORTED_MEDIA_TYPE",
                                    "message": f"Content-Type '{content_type}' is not supported",
                                    "details": {
                                        "allowed_types": list(ALLOWED_CONTENT_TYPES)
                                    }
                                }
                            }
                        )
            
            # 2. Validate request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_REQUEST_SIZE:
                logger.warning(
                    f"Request too large: {content_length} bytes for {request.url.path}"
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": {
                            "code": "REQUEST_TOO_LARGE",
                            "message": "Request body too large",
                            "details": {
                                "max_size_bytes": MAX_REQUEST_SIZE,
                                "request_size_bytes": int(content_length)
                            }
                        }
                    }
                )
            
            # 3. Pre-parse JSON to catch malformed JSON early
            if request.headers.get("content-type", "").startswith("application/json"):
                # Store the body for later use
                body = await request.body()
                
                if body:
                    try:
                        # Validate JSON structure
                        json.loads(body)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Malformed JSON in request to {request.url.path}: {e}"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                "error": {
                                    "code": "MALFORMED_JSON",
                                    "message": "Invalid JSON in request body",
                                    "details": {
                                        "error": str(e),
                                        "position": e.pos if hasattr(e, 'pos') else None
                                    }
                                }
                            }
                        )
                
                # Create new request with the stored body
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
            
            # Process the request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Error in request validation middleware: {e}")
            # Don't block the request on middleware errors
            return await call_next(request)


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string value by:
    - Stripping leading/trailing whitespace
    - Limiting length
    - Removing null characters
    """
    if not isinstance(value, str):
        return value
    
    # Remove null characters
    value = value.replace('\x00', '')
    
    # Strip whitespace
    value = value.strip()
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def sanitize_dict(data: dict, max_string_length: int = 1000) -> dict:
    """
    Recursively sanitize all string values in a dictionary.
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value, max_string_length)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, max_string_length)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, max_string_length) if isinstance(item, dict)
                else sanitize_string(item, max_string_length) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized