"""
Document Lifecycle Custom Exceptions.

This module defines custom exceptions for the document lifecycle management system,
providing clear, domain-specific error handling.
"""


class DocumentLifecycleError(Exception):
    """Base exception for all document lifecycle errors."""

    pass


class DocumentNotFoundError(DocumentLifecycleError):
    """Raised when a requested document does not exist in the registry."""

    def __init__(self, message: str, doc_id: int = None, path: str = None):
        """
        Initialize DocumentNotFoundError.

        Args:
            message: Error message
            doc_id: Optional document ID that was not found
            path: Optional document path that was not found
        """
        super().__init__(message)
        self.doc_id = doc_id
        self.path = path


class DocumentAlreadyExistsError(DocumentLifecycleError):
    """Raised when attempting to register a document with a duplicate path."""

    def __init__(self, message: str, path: str = None):
        """
        Initialize DocumentAlreadyExistsError.

        Args:
            message: Error message
            path: Optional document path that already exists
        """
        super().__init__(message)
        self.path = path


class ValidationError(DocumentLifecycleError):
    """Raised when invalid data is provided to a lifecycle operation."""

    def __init__(self, message: str, field: str = None, value=None):
        """
        Initialize ValidationError.

        Args:
            message: Error message
            field: Optional field name that failed validation
            value: Optional value that failed validation
        """
        super().__init__(message)
        self.field = field
        self.value = value


class RelationshipError(DocumentLifecycleError):
    """Raised when a document relationship operation fails."""

    def __init__(
        self,
        message: str,
        parent_id: int = None,
        child_id: int = None,
        relationship_type: str = None,
    ):
        """
        Initialize RelationshipError.

        Args:
            message: Error message
            parent_id: Optional parent document ID
            child_id: Optional child document ID
            relationship_type: Optional relationship type
        """
        super().__init__(message)
        self.parent_id = parent_id
        self.child_id = child_id
        self.relationship_type = relationship_type


class DatabaseError(DocumentLifecycleError):
    """Raised when a database operation fails."""

    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize DatabaseError.

        Args:
            message: Error message
            original_error: Optional original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class InvalidStateTransition(DocumentLifecycleError):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self, message: str, from_state: str = None, to_state: str = None, doc_id: int = None
    ):
        """
        Initialize InvalidStateTransition.

        Args:
            message: Error message
            from_state: Optional current state
            to_state: Optional target state
            doc_id: Optional document ID
        """
        super().__init__(message)
        self.from_state = from_state
        self.to_state = to_state
        self.doc_id = doc_id
