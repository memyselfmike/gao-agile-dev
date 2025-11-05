"""
Custom exceptions for the checklist system.

Provides specific exception types for different error conditions
in checklist loading, validation, and inheritance resolution.
"""


class ChecklistError(Exception):
    """Base exception for all checklist-related errors."""

    pass


class ChecklistNotFoundError(ChecklistError):
    """Raised when a checklist file cannot be found."""

    pass


class ChecklistInheritanceError(ChecklistError):
    """Raised when there are issues with checklist inheritance (e.g., circular dependencies)."""

    pass


class ChecklistValidationError(ChecklistError):
    """Raised when a checklist fails schema validation."""

    pass
