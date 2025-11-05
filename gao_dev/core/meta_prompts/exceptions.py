"""
Exceptions for meta-prompt reference resolution.
"""


class ReferenceResolutionError(Exception):
    """Base exception for reference resolution errors."""
    pass


class InvalidReferenceError(ReferenceResolutionError):
    """Raised when reference syntax is invalid."""
    pass


class ResolverNotFoundError(ReferenceResolutionError):
    """Raised when no resolver found for reference type."""
    pass


class CircularReferenceError(ReferenceResolutionError):
    """Raised when circular reference detected."""
    pass


class MaxDepthExceededError(ReferenceResolutionError):
    """Raised when maximum nesting depth exceeded."""
    pass
