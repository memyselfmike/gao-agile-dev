"""
Registry for reference resolvers with nested resolution support.
"""

import re
from datetime import timedelta
from typing import Dict, Any, Set
import structlog

from .reference_resolver import ReferenceResolver
from .resolver_cache import ResolverCache
from .exceptions import (
    InvalidReferenceError,
    ResolverNotFoundError,
    CircularReferenceError,
    MaxDepthExceededError,
)

logger = structlog.get_logger(__name__)


class ReferenceResolverRegistry:
    """Registry of all reference resolvers with nested resolution support."""

    # Pattern to match references: @type:value
    REFERENCE_PATTERN = re.compile(r'@([a-zA-Z_][a-zA-Z0-9_]*):([^\s]+)')

    def __init__(
        self,
        cache_ttl: timedelta = timedelta(minutes=5),
        cache_max_size: int = 100,
        max_depth: int = 3
    ):
        """
        Initialize resolver registry.

        Args:
            cache_ttl: Time-to-live for cached references
            cache_max_size: Maximum number of cached references
            max_depth: Maximum nesting depth for nested references
        """
        self._resolvers: Dict[str, ReferenceResolver] = {}
        self._cache = ResolverCache(ttl=cache_ttl, max_size=cache_max_size)
        self._max_depth = max_depth
        logger.info(
            "resolver_registry_initialized",
            max_depth=max_depth,
            cache_ttl_seconds=cache_ttl.total_seconds()
        )

    def register(self, resolver: ReferenceResolver) -> None:
        """
        Register a new resolver.

        Args:
            resolver: Resolver instance to register
        """
        resolver_type = resolver.get_type()
        self._resolvers[resolver_type] = resolver
        logger.info("resolver_registered", type=resolver_type)

    def resolve(
        self,
        reference: str,
        context: Dict[str, Any],
        _depth: int = 0,
        _visited: Set[str] = None
    ) -> str:
        """
        Resolve a reference using the appropriate resolver.

        Handles caching, error handling, and nested references.

        Args:
            reference: Full reference string (e.g., "@doc:path/to/file.md")
            context: Context dict with variables for resolution
            _depth: Current recursion depth (internal)
            _visited: Set of visited references (internal)

        Returns:
            Resolved content as string

        Raises:
            InvalidReferenceError: If reference syntax is invalid
            ResolverNotFoundError: If no resolver found for type
            CircularReferenceError: If circular reference detected
            MaxDepthExceededError: If max nesting depth exceeded
        """
        # Initialize visited set on first call
        if _visited is None:
            _visited = set()

        # Check for circular references
        if reference in _visited:
            raise CircularReferenceError(
                f"Circular reference detected: {reference}"
            )

        # Check max depth
        if _depth >= self._max_depth:
            raise MaxDepthExceededError(
                f"Maximum nesting depth ({self._max_depth}) exceeded"
            )

        # Check cache
        cached = self._cache.get(reference)
        if cached is not None:
            logger.debug("resolved_from_cache", reference=reference)
            return cached

        # Parse reference
        ref_type, ref_value = self.parse_reference(reference)

        # Find resolver
        resolver = self._resolvers.get(ref_type)
        if resolver is None:
            raise ResolverNotFoundError(
                f"No resolver found for type: {ref_type}"
            )

        # Mark as visited
        _visited.add(reference)

        try:
            # Resolve
            logger.debug(
                "resolving_reference",
                type=ref_type,
                value=ref_value,
                depth=_depth
            )
            content = resolver.resolve(ref_value, context)

            # Resolve nested references recursively
            content = self._resolve_nested(
                content, context, _depth, _visited
            )

            # Cache result (only cache at top level)
            if _depth == 0:
                self._cache.set(reference, content)

            logger.debug(
                "reference_resolved",
                reference=reference,
                content_length=len(content)
            )
            return content

        finally:
            # Remove from visited on backtrack
            _visited.discard(reference)

    def parse_reference(self, reference: str) -> tuple[str, str]:
        """
        Parse reference into (type, value).

        Args:
            reference: Full reference string (e.g., "@doc:path/to/file.md")

        Returns:
            Tuple of (type, value)

        Raises:
            InvalidReferenceError: If syntax is invalid

        Examples:
            @doc:path/to/file.md -> ("doc", "path/to/file.md")
            @checklist:testing/unit-test-standards ->
                ("checklist", "testing/unit-test-standards")
        """
        if not reference.startswith('@'):
            raise InvalidReferenceError(
                f"Reference must start with '@': {reference}"
            )

        match = self.REFERENCE_PATTERN.match(reference)
        if not match:
            raise InvalidReferenceError(
                f"Invalid reference syntax: {reference}"
            )

        ref_type = match.group(1)
        ref_value = match.group(2)

        return ref_type, ref_value

    def _find_references(self, content: str) -> list[str]:
        """
        Find all references in content.

        Args:
            content: Content to search for references

        Returns:
            List of reference strings found
        """
        matches = self.REFERENCE_PATTERN.findall(content)
        references = [f"@{ref_type}:{ref_value}"
                     for ref_type, ref_value in matches]
        return references

    def _resolve_nested(
        self,
        content: str,
        context: Dict[str, Any],
        depth: int,
        visited: Set[str]
    ) -> str:
        """
        Resolve nested references in content.

        Args:
            content: Content that may contain references
            context: Context dict for resolution
            depth: Current recursion depth
            visited: Set of visited references

        Returns:
            Content with all nested references resolved
        """
        # Check max depth before processing nested references
        if depth >= self._max_depth:
            return content

        references = self._find_references(content)

        for ref in references:
            try:
                # Pass depth + 1 for nested resolution
                resolved = self.resolve(ref, context, depth + 1, visited)
                content = content.replace(ref, resolved)
            except (CircularReferenceError, MaxDepthExceededError):
                # Re-raise these critical errors
                raise
            except Exception as e:
                # Log warning but don't fail entire resolution for other errors
                logger.warning(
                    "nested_reference_failed",
                    reference=ref,
                    error=str(e),
                    depth=depth
                )
                # Replace with empty string
                content = content.replace(ref, "")

        return content

    def invalidate_cache(self, reference: str = None) -> None:
        """
        Invalidate cache entries.

        Args:
            reference: Specific reference to invalidate, or None to clear all
        """
        if reference:
            self._cache.invalidate(reference)
        else:
            self._cache.clear()

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        return self._cache.get_stats()

    def list_resolvers(self) -> list[str]:
        """
        List all registered resolver types.

        Returns:
            List of resolver type strings
        """
        return list(self._resolvers.keys())
