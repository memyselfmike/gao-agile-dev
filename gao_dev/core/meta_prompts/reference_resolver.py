"""
Base class and interface for reference resolvers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class ReferenceResolver(ABC):
    """Base class for reference resolvers."""

    @abstractmethod
    def resolve(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Resolve a reference to its content.

        Args:
            reference: The reference value (e.g., "path/to/file.md")
            context: Context dict with variables for resolution

        Returns:
            Resolved content as string

        Raises:
            ReferenceResolutionError: If resolution fails
        """
        pass

    @abstractmethod
    def can_resolve(self, reference_type: str) -> bool:
        """
        Check if this resolver can handle the reference type.

        Args:
            reference_type: Type of reference (e.g., "doc", "checklist")

        Returns:
            True if this resolver can handle the type
        """
        pass

    def get_type(self) -> str:
        """
        Get the reference type this resolver handles.

        Returns:
            Reference type string (e.g., "doc", "checklist")
        """
        return self.__class__.__name__.replace("Resolver", "").lower()
