"""Custom exceptions for state tracking.

Provides specialized exceptions for state tracker operations with clear
error messages and type safety.
"""


class StateTrackerError(Exception):
    """Base exception for state tracker errors.

    All state tracker exceptions inherit from this base class for
    consistent error handling.
    """

    pass


class RecordNotFoundError(StateTrackerError):
    """Raised when a requested record is not found in database.

    This exception indicates a query for a specific entity (story, epic, etc.)
    returned no results.
    """

    pass


class ValidationError(StateTrackerError):
    """Raised when data validation fails.

    This exception indicates invalid data was provided, such as:
    - Invalid status values
    - Invalid priority levels
    - Invalid date formats
    - Constraint violations
    """

    pass


class DatabaseConnectionError(StateTrackerError):
    """Raised when database connection fails.

    This exception indicates issues with database connectivity or
    initialization.
    """

    pass


class TransactionError(StateTrackerError):
    """Raised when database transaction fails.

    This exception indicates a transaction could not be completed and
    was rolled back.
    """

    pass
