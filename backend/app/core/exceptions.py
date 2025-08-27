"""Custom exceptions for the chores tracker application."""


class ChoresTrackerException(Exception):
    """Base exception for all chores tracker specific errors."""
    pass


class ValidationError(ChoresTrackerException):
    """Raised when validation fails."""
    pass


class NotFoundError(ChoresTrackerException):
    """Raised when a requested resource is not found."""
    pass


class AuthorizationError(ChoresTrackerException):
    """Raised when user lacks permission for an operation."""
    pass


class DuplicateError(ChoresTrackerException):
    """Raised when attempting to create a duplicate resource."""
    pass


class BusinessRuleError(ChoresTrackerException):
    """Raised when business rules are violated."""
    pass