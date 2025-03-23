from datetime import datetime, timedelta
from typing import Any, Optional

from jose import jwt

from ...core.config import settings

def create_access_token(
    subject: Any, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify a token and return the user ID if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.JWTError:
        return None