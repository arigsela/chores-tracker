"""
Registration code validation utilities for beta access control.

This module provides functionality to validate registration codes during
the beta period. This is a temporary measure and should be removed or
modified when the application goes to general availability.
"""

from fastapi import HTTPException, status
from typing import Optional
from ..core.config import settings


def validate_registration_code(
    registration_code: Optional[str],
    is_parent: bool,
    bypass_for_children: bool = True
) -> bool:
    """
    Validate registration code for new user registration.
    
    Args:
        registration_code: The registration code provided by the user
        is_parent: Whether this is a parent account registration
        bypass_for_children: If True, children don't need registration codes
        
    Returns:
        bool: True if validation passes
        
    Raises:
        HTTPException: If validation fails
    """
    # During beta, only parent registrations need codes
    if not is_parent and bypass_for_children:
        return True
    
    # Parent accounts require registration codes during beta
    if is_parent:
        if not registration_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Registration code is required during beta period"
            )
        
        if not registration_code.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Registration code cannot be empty"
            )
        
        # Check if the code is valid (case-insensitive)
        valid_codes = settings.VALID_REGISTRATION_CODES
        provided_code = registration_code.strip().upper()
        
        if provided_code not in valid_codes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid registration code. Please contact admin for a valid beta code."
            )
    
    return True


def get_valid_registration_codes() -> list[str]:
    """
    Get the list of valid registration codes for admin purposes.
    
    Returns:
        list[str]: List of valid registration codes
    """
    return settings.VALID_REGISTRATION_CODES


def is_registration_restricted() -> bool:
    """
    Check if registration is currently restricted by codes.
    
    Returns:
        bool: True if registration codes are required
    """
    # Registration is restricted if we have any codes configured
    return len(settings.VALID_REGISTRATION_CODES) > 0