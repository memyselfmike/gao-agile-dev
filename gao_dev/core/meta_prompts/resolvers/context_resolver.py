"""
Context reference resolver for @context: references.

This resolver integrates with the ContextCache to inject frequently used context
into prompts. It supports predefined context keys (epic_definition, architecture)
and custom context keys from the context dict.
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import structlog

from gao_dev.core.meta_prompts.reference_resolver import ReferenceResolver
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager

logger = structlog.get_logger(__name__)


class ContextResolver(ReferenceResolver):
    """
    Resolver for @context: references.

    This resolver loads context from cache (for performance) with fallback
    to DocumentLifecycleManager. It supports predefined context keys that
    map to specific documents, as well as custom context keys from the
    context dictionary.

    Predefined Context Keys:
        - epic_definition: Epic definition from epics.md
        - architecture: Architecture documentation
        - prd: Product Requirements Document
        - coding_standards: Coding standards document
        - acceptance_criteria: Story acceptance criteria
        - story_definition: Full story document

    Custom Context Keys:
        Any key in the context dict can be referenced directly.

    Examples:
        >>> resolver = ContextResolver(cache, doc_manager, tracker)
        >>>
        >>> # Load epic definition (cached)
        >>> context = {'feature': 'sandbox', 'epic': 3}
        >>> epic = resolver.resolve("epic_definition", context)
        >>>
        >>> # Load architecture (cached)
        >>> arch = resolver.resolve("architecture", context)
        >>>
        >>> # Custom context key
        >>> context = {'custom_guidelines': 'Use TDD approach...'}
        >>> guidelines = resolver.resolve("custom_guidelines", context)

    Args:
        context_cache: Cache for storing frequently accessed context
        doc_manager: Document lifecycle manager for loading documents
        context_tracker: Tracker for recording context usage
        project_root: Project root directory for resolving paths
    """

    # Predefined context keys with their document path mappings
    # Each mapping is a function that takes context dict and returns document path
    CONTEXT_MAPPINGS: Dict[str, Callable[[Dict[str, Any]], str]] = {
        'epic_definition': lambda ctx: f"docs/features/{ctx['feature']}/epics.md#epic-{ctx['epic']}",
        'architecture': lambda ctx: f"docs/features/{ctx['feature']}/ARCHITECTURE.md",
        'prd': lambda ctx: f"docs/features/{ctx['feature']}/PRD.md",
        'coding_standards': lambda ctx: "docs/CODING_STANDARDS.md",
        'acceptance_criteria': lambda ctx: f"docs/features/{ctx['feature']}/stories/epic-{ctx['epic']}/story-{ctx['story']}.md#acceptance-criteria",
        'story_definition': lambda ctx: f"docs/features/{ctx['feature']}/stories/epic-{ctx['epic']}/story-{ctx['story']}.md",
    }

    def __init__(
        self,
        context_cache: ContextCache,
        doc_manager: DocumentLifecycleManager,
        context_tracker: ContextUsageTracker,
        project_root: Optional[Path] = None
    ):
        """
        Initialize context resolver.

        Args:
            context_cache: Cache for context storage
            doc_manager: Document lifecycle manager
            context_tracker: Usage tracker for audit trail
            project_root: Project root directory (optional)
        """
        self.cache = context_cache
        self.doc_manager = doc_manager
        self.tracker = context_tracker
        self.project_root = project_root or Path.cwd()

    def can_resolve(self, reference_type: str) -> bool:
        """
        Check if this resolver can handle the reference type.

        Args:
            reference_type: Type of reference (e.g., "context", "doc")

        Returns:
            True if type is "context"
        """
        return reference_type == "context"

    def resolve(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Resolve @context: reference to context content.

        Resolution order:
        1. Check cache for the context key
        2. If cache miss, load from document (for predefined keys)
        3. If not predefined, check context dict for custom key
        4. If not found, return empty string with warning

        Args:
            reference: Context key (e.g., "epic_definition", "architecture")
            context: Context dict with variables for resolution

        Returns:
            Resolved context content as string

        Example:
            >>> resolver.resolve("epic_definition", {
            ...     'feature': 'sandbox',
            ...     'epic': 3,
            ...     'workflow_id': 'wf-123'
            ... })
            # Returns cached epic definition or loads from file
        """
        logger.debug("resolving_context_reference", reference=reference)

        # Build cache key including context variables for uniqueness
        cache_key = self._build_cache_key(reference, context)

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("context_cache_hit", reference=reference, cache_key=cache_key)
            self._track_usage(reference, cached, context, cache_hit=True)
            return cached

        # Cache miss - load content
        logger.debug("context_cache_miss", reference=reference, cache_key=cache_key)
        content = self._load_context(reference, context)

        # Cache the result if content was found
        if content:
            self.cache.set(cache_key, content)
        else:
            logger.warning("context_not_found", reference=reference)

        self._track_usage(reference, content, context, cache_hit=False)
        return content

    def _build_cache_key(self, reference: str, context: Dict[str, Any]) -> str:
        """
        Build cache key from reference and context variables.

        For predefined keys, includes relevant context vars (feature, epic, story).
        For custom keys, just uses the reference name.

        Args:
            reference: Context key
            context: Context dict

        Returns:
            Cache key string
        """
        if reference in self.CONTEXT_MAPPINGS:
            # Include context variables that affect the document path
            parts = [reference]

            if 'feature' in context:
                parts.append(f"feature={context['feature']}")
            if 'epic' in context:
                parts.append(f"epic={context['epic']}")
            if 'story' in context:
                parts.append(f"story={context['story']}")

            return ":".join(parts)
        else:
            # Custom key - just use reference name
            return f"custom:{reference}"

    def _load_context(self, key: str, context: Dict[str, Any]) -> str:
        """
        Load context from document or context dict.

        Resolution order:
        1. Predefined context key -> load from document
        2. Custom context key -> get from context dict
        3. Not found -> return empty string

        Args:
            key: Context key
            context: Context dict

        Returns:
            Context content as string, or empty string if not found
        """
        # Check if predefined context key
        if key in self.CONTEXT_MAPPINGS:
            return self._load_predefined_context(key, context)

        # Custom context key - try to load from context dict
        elif key in context:
            value = context[key]
            logger.debug("custom_context_loaded", key=key, value_type=type(value).__name__)
            return str(value)

        else:
            logger.warning("unknown_context_key", key=key)
            return ""

    def _load_predefined_context(self, key: str, context: Dict[str, Any]) -> str:
        """
        Load predefined context key from document.

        Uses CONTEXT_MAPPINGS to resolve the document path, then loads
        the document content.

        Args:
            key: Predefined context key
            context: Context dict with variables (feature, epic, story)

        Returns:
            Document content, or empty string if document not found
        """
        # Get path mapping function
        path_func = self.CONTEXT_MAPPINGS[key]

        # Resolve document path
        try:
            doc_path = path_func(context)
        except KeyError as e:
            logger.warning(
                "missing_context_variable",
                key=key,
                missing_var=str(e)
            )
            return ""

        logger.debug("loading_context_document", key=key, doc_path=doc_path)

        # Handle section references (path#section)
        if "#" in doc_path:
            # This is a section reference - delegate to doc resolver logic
            path, section = doc_path.split("#", 1)
            content = self._read_file(Path(path))
            if content:
                return self._extract_markdown_section(content, section)
            return ""
        else:
            # Full document
            return self._read_file(Path(doc_path))

    def _read_file(self, path: Path) -> str:
        """
        Read file content from filesystem.

        Resolves path relative to project root if not absolute.

        Args:
            path: File path (relative or absolute)

        Returns:
            File content as string, or empty string if not found
        """
        # Resolve relative to project root
        if not path.is_absolute():
            full_path = (self.project_root / path).resolve()
        else:
            full_path = path

        # Check if file exists
        if not full_path.exists():
            logger.warning("file_not_found", path=str(full_path))
            return ""

        try:
            return full_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(
                "file_read_error",
                path=str(full_path),
                error=str(e)
            )
            return ""

    def _extract_markdown_section(self, content: str, heading: str) -> str:
        """
        Extract markdown section by heading.

        Uses the same algorithm as DocResolver for consistency.

        Args:
            content: Full markdown content
            heading: Heading slug (e.g., "acceptance-criteria")

        Returns:
            Section content with formatting preserved
        """
        import re

        lines = content.split('\n')
        heading_slug = self._normalize_heading(heading)

        in_section = False
        section_lines = []
        section_level = None

        for line in lines:
            # Check if this is a heading line
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                title_slug = self._normalize_heading(title)

                if title_slug == heading_slug:
                    # Found the section start
                    in_section = True
                    section_level = level
                elif in_section and level <= section_level:
                    # Reached next section at same or higher level - stop
                    break
            elif in_section:
                # Collect content lines
                section_lines.append(line)

        result = '\n'.join(section_lines).strip()

        if not result:
            logger.warning(
                "section_not_found",
                heading=heading,
                heading_slug=heading_slug
            )

        return result

    def _normalize_heading(self, heading: str) -> str:
        """
        Normalize heading to slug format.

        Converts to lowercase, replaces spaces with hyphens, removes special chars.

        Args:
            heading: Original heading text

        Returns:
            Normalized slug

        Examples:
            "Acceptance Criteria" -> "acceptance-criteria"
            "User Stories" -> "user-stories"
        """
        import re

        # Convert to lowercase
        slug = heading.lower()

        # Replace spaces and underscores with hyphens
        slug = slug.replace(' ', '-').replace('_', '-')

        # Remove special characters except hyphens and alphanumeric
        slug = re.sub(r'[^a-z0-9-]', '', slug)

        # Remove consecutive hyphens
        slug = re.sub(r'-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        return slug

    def _track_usage(
        self,
        context_key: str,
        content: str,
        context: Dict[str, Any],
        cache_hit: bool
    ) -> None:
        """
        Track context usage for audit trail.

        Records the context key, workflow ID, epic/story, content hash,
        and cache hit status.

        Args:
            context_key: Context key that was resolved
            content: Resolved content
            context: Context dict with workflow metadata
            cache_hit: Whether content was loaded from cache
        """
        self.tracker.record_usage(
            context_key=context_key,
            workflow_id=context.get('workflow_id'),
            epic=context.get('epic'),
            story=context.get('story'),
            content_hash=self._hash_content(content),
            cache_hit=cache_hit
        )

    def _hash_content(self, content: str) -> str:
        """
        Hash content for version tracking.

        Uses SHA-256 hash, truncated to 16 characters for readability.

        Args:
            content: Content to hash

        Returns:
            Hex hash string (16 chars)
        """
        return hashlib.sha256(content.encode()).hexdigest()[:16]
