"""
Exceptions for context persistence operations.

This module provides custom exceptions for context persistence layer errors,
including database operations, serialization, and context retrieval failures.
"""


class PersistenceError(Exception):
    """
    Raised when context persistence operation fails.

    This exception is raised when database operations fail, including
    connection errors, query errors, transaction errors, and serialization
    failures.

    Example:
        >>> try:
        ...     persistence.save_context(context)
        ... except PersistenceError as e:
        ...     print(f"Failed to save context: {e}")
    """

    pass


class ContextNotFoundError(Exception):
    """
    Raised when requested context is not found in database.

    This exception is raised when attempting to load a context that does not
    exist in the database, or when a query returns no results.

    Example:
        >>> try:
        ...     context = persistence.load_context("invalid-id")
        ... except ContextNotFoundError as e:
        ...     print(f"Context not found: {e}")
    """

    pass
