"""
Context API for agents to access context without manual document loading.

This module provides a simple, high-level API for agents to access project context
(PRDs, architecture, epic definitions, etc.) with automatic caching, lazy loading,
and usage tracking. Agents can use this API without worrying about file paths,
cache management, or document loading.

Example:
    >>> # Get current workflow context
    >>> context = get_workflow_context()
    >>>
    >>> # Lazy-loaded, cached, tracked access
    >>> epic_def = context.get_epic_definition()
    >>> architecture = context.get_architecture()
    >>> standards = context.get_coding_standards()
    >>>
    >>> # Use in agent prompt
    >>> prompt = f'''
    ... Epic Definition:
    ... {epic_def}
    ...
    ... Architecture:
    ... {architecture}
    ... '''
"""

import hashlib
import threading
from datetime import timedelta
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import structlog

from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import DocumentType, DocumentState

logger = structlog.get_logger(__name__)

# Thread-local storage for current workflow context
_thread_local = threading.local()

# Global instances (singleton pattern)
_global_cache: Optional[ContextCache] = None
_global_tracker: Optional[ContextUsageTracker] = None


def _get_global_cache() -> ContextCache:
    """
    Get or create global ContextCache instance.

    Returns:
        Shared ContextCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ContextCache(
            ttl=timedelta(minutes=5),
            max_size=100
        )
    return _global_cache


def _get_global_tracker(db_path: Optional[Path] = None) -> ContextUsageTracker:
    """
    Get or create global ContextUsageTracker instance.

    Args:
        db_path: Optional path to usage tracking database

    Returns:
        Shared ContextUsageTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        if db_path is None:
            db_path = Path.cwd() / ".gao" / "context_usage.db"
        _global_tracker = ContextUsageTracker(db_path)
    return _global_tracker


def _reset_global_instances() -> None:
    """
    Reset global cache and tracker instances.

    This is primarily for testing purposes to ensure clean state.
    """
    global _global_cache, _global_tracker
    _global_cache = None
    _global_tracker = None


def set_workflow_context(context: WorkflowContext) -> None:
    """
    Set the current workflow context (thread-local).

    Args:
        context: WorkflowContext to set as current
    """
    _thread_local.context = context
    logger.debug("workflow_context_set", workflow_id=context.workflow_id)


def get_workflow_context() -> Optional[WorkflowContext]:
    """
    Get the current workflow context (thread-local).

    Returns:
        Current WorkflowContext or None if not set

    Example:
        >>> context = get_workflow_context()
        >>> if context:
        ...     epic_def = context.get_epic_definition()
    """
    return getattr(_thread_local, "context", None)


def clear_workflow_context() -> None:
    """
    Clear the current workflow context (thread-local).

    Useful for cleanup after workflow execution.
    """
    if hasattr(_thread_local, "context"):
        delattr(_thread_local, "context")
        logger.debug("workflow_context_cleared")


class AgentContextAPI:
    """
    High-level API for agents to access context with automatic caching and tracking.

    This class wraps WorkflowContext, ContextCache, and ContextUsageTracker to
    provide a simple interface for agents. All document access is lazy-loaded,
    cached, and tracked automatically.

    Features:
    - Lazy loading: Documents loaded only when accessed
    - Transparent caching: Automatic cache usage with fallback to file loading
    - Usage tracking: Every access recorded for audit trail
    - Custom loaders: Support for custom document loading logic

    Example:
        >>> # Create API instance
        >>> api = AgentContextAPI(workflow_context)
        >>>
        >>> # Access documents (lazy-loaded, cached, tracked)
        >>> epic = api.get_epic_definition()
        >>> arch = api.get_architecture()
        >>> standards = api.get_coding_standards()
        >>>
        >>> # Custom context keys
        >>> api.set_custom("project_name", "MyApp")
        >>> name = api.get_custom("project_name")
    """

    def __init__(
        self,
        workflow_context: WorkflowContext,
        cache: Optional[ContextCache] = None,
        tracker: Optional[ContextUsageTracker] = None,
        document_loader: Optional[Callable[[str, WorkflowContext], Optional[str]]] = None
    ):
        """
        Initialize AgentContextAPI.

        Args:
            workflow_context: WorkflowContext for this execution
            cache: Optional ContextCache instance (uses global if None)
            tracker: Optional ContextUsageTracker instance (uses global if None)
            document_loader: Optional custom document loader function
        """
        self.workflow_context = workflow_context
        self.cache = cache or _get_global_cache()
        self.tracker = tracker or _get_global_tracker()
        self.document_loader = document_loader or self._default_document_loader
        self._custom_context: Dict[str, Any] = {}

        logger.debug(
            "agent_context_api_initialized",
            workflow_id=workflow_context.workflow_id,
            story_id=workflow_context.story_id
        )

    def get_epic_definition(self) -> Optional[str]:
        """
        Get epic definition (lazy-loaded, cached, tracked).

        Returns:
            Epic definition content or None if not available
        """
        return self._get_document("epic_definition")

    def get_architecture(self) -> Optional[str]:
        """
        Get architecture document (lazy-loaded, cached, tracked).

        Returns:
            Architecture content or None if not available
        """
        return self._get_document("architecture")

    def get_prd(self) -> Optional[str]:
        """
        Get PRD document (lazy-loaded, cached, tracked).

        Returns:
            PRD content or None if not available
        """
        return self._get_document("prd")

    def get_story_definition(self) -> Optional[str]:
        """
        Get story definition (lazy-loaded, cached, tracked).

        Returns:
            Story definition content or None if story_num is None or not available
        """
        if self.workflow_context.story_num is None:
            return None
        return self._get_document("story_definition")

    def get_coding_standards(self) -> Optional[str]:
        """
        Get coding standards document (lazy-loaded, cached, tracked).

        Returns:
            Coding standards content or None if not available
        """
        return self._get_document("coding_standards")

    def get_acceptance_criteria(self) -> Optional[str]:
        """
        Get acceptance criteria (lazy-loaded, cached, tracked).

        Returns:
            Acceptance criteria content or None if not available
        """
        return self._get_document("acceptance_criteria")

    def get_custom(self, key: str, default: Any = None) -> Any:
        """
        Get custom context value.

        Args:
            key: Custom context key
            default: Default value if key not found

        Returns:
            Custom context value or default
        """
        return self._custom_context.get(key, default)

    def set_custom(self, key: str, value: Any) -> None:
        """
        Set custom context value.

        Args:
            key: Custom context key
            value: Value to store
        """
        self._custom_context[key] = value
        logger.debug("custom_context_set", key=key)

    def _get_document(self, doc_type: str) -> Optional[str]:
        """
        Get document with caching and tracking.

        This method:
        1. Generates cache key from doc_type and workflow context
        2. Checks cache first
        3. If cache miss, loads document using loader
        4. Caches the result
        5. Records usage in tracker
        6. Returns content

        Args:
            doc_type: Type of document (epic_definition, architecture, etc.)

        Returns:
            Document content or None if not available
        """
        # Generate cache key
        cache_key = self._generate_cache_key(doc_type)

        # Try cache first
        cached_content = self.cache.get(cache_key)
        cache_hit = cached_content is not None

        if cache_hit:
            content = cached_content
            logger.debug("cache_hit", doc_type=doc_type, cache_key=cache_key)
        else:
            # Load document
            content = self.document_loader(doc_type, self.workflow_context)

            # Cache it if loaded
            if content is not None:
                self.cache.set(cache_key, content)
                logger.debug("document_cached", doc_type=doc_type, cache_key=cache_key)
            else:
                logger.debug("document_not_found", doc_type=doc_type)

        # Track usage
        if content is not None:
            content_hash = self._hash_content(content)
            self.tracker.record_usage(
                context_key=doc_type,
                content_hash=content_hash,
                cache_hit=cache_hit,
                workflow_id=self.workflow_context.workflow_id,
                epic=self.workflow_context.epic_num,
                story=self.workflow_context.story_id
            )

        return content

    def _generate_cache_key(self, doc_type: str) -> str:
        """
        Generate cache key from doc_type and workflow context.

        Args:
            doc_type: Type of document

        Returns:
            Cache key string
        """
        # Include feature, epic, story in cache key for uniqueness
        return f"{self.workflow_context.feature}:{self.workflow_context.story_id}:{doc_type}"

    def _hash_content(self, content: str) -> str:
        """
        Generate hash of content for version tracking.

        Args:
            content: Content to hash

        Returns:
            SHA256 hash hex string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def _default_document_loader(
        self,
        doc_type: str,
        workflow_context: WorkflowContext
    ) -> Optional[str]:
        """
        Default document loader implementation with DocumentLifecycleManager integration.

        This method integrates with DocumentLifecycleManager (Epic 12) to load
        documents from the registry. Falls back to file-based loading if registry
        access fails.

        Args:
            doc_type: Type of document to load
            workflow_context: Workflow context with feature/epic/story info

        Returns:
            Document content or None if not found
        """
        # Map doc_type string to DocumentType enum
        doc_type_map = {
            "prd": DocumentType.PRD,
            "architecture": DocumentType.ARCHITECTURE,
            "epic_definition": DocumentType.EPIC,
            "story_definition": DocumentType.STORY,
        }

        document_type = doc_type_map.get(doc_type)

        # Try loading from DocumentLifecycleManager if we have a mapped type
        if document_type is not None:
            content = self._load_from_lifecycle_manager(
                document_type,
                workflow_context
            )
            if content is not None:
                return content

        # Fall back to file-based loading
        return self._load_from_filesystem(doc_type, workflow_context)

    def _load_from_lifecycle_manager(
        self,
        document_type: DocumentType,
        workflow_context: WorkflowContext
    ) -> Optional[str]:
        """
        Load document from DocumentLifecycleManager registry.

        Args:
            document_type: DocumentType enum value
            workflow_context: Workflow context with feature info

        Returns:
            Document content or None if not found
        """
        try:
            # Initialize registry and manager
            db_path = Path.cwd() / ".gao" / "documents.db"
            if not db_path.exists():
                logger.debug("document_registry_not_found", db_path=str(db_path))
                return None

            registry = DocumentRegistry(db_path)
            manager = DocumentLifecycleManager(
                registry=registry,
                archive_dir=Path.cwd() / ".gao" / ".archive"
            )

            # Query for active document
            document = manager.get_current_document(
                doc_type=document_type.value,
                feature=workflow_context.feature
            )

            # Close registry connection
            registry.close()

            if document is None:
                logger.debug(
                    "document_not_found_in_registry",
                    doc_type=document_type.value,
                    feature=workflow_context.feature
                )
                return None

            # Load content from file
            doc_path = Path(document.path)
            if not doc_path.exists():
                logger.warning(
                    "document_path_not_found",
                    path=str(doc_path),
                    doc_type=document_type.value
                )
                return None

            content = doc_path.read_text(encoding='utf-8')
            logger.debug(
                "document_loaded_from_registry",
                doc_type=document_type.value,
                path=str(doc_path)
            )
            return content

        except Exception as e:
            logger.debug(
                "lifecycle_manager_load_failed",
                doc_type=document_type.value,
                error=str(e)
            )
            return None

    def _load_from_filesystem(
        self,
        doc_type: str,
        workflow_context: WorkflowContext
    ) -> Optional[str]:
        """
        Load document directly from filesystem (fallback).

        Uses standard docs/features directory structure.

        Args:
            doc_type: Type of document
            workflow_context: Workflow context with feature/epic/story info

        Returns:
            Document content or None if not found
        """
        # Map doc_type to file path
        docs_base = Path.cwd() / "docs" / "features" / workflow_context.feature

        file_path: Optional[Path] = None

        if doc_type == "prd":
            file_path = docs_base / "PRD.md"
        elif doc_type == "architecture":
            file_path = docs_base / "ARCHITECTURE.md"
        elif doc_type == "epic_definition":
            file_path = docs_base / "epics" / f"epic-{workflow_context.epic_num}.md"
        elif doc_type == "story_definition":
            if workflow_context.story_num is not None:
                file_path = (
                    docs_base / "stories" / f"epic-{workflow_context.epic_num}" /
                    f"story-{workflow_context.epic_num}.{workflow_context.story_num}.md"
                )
        elif doc_type == "coding_standards":
            file_path = Path.cwd() / "docs" / "CODING_STANDARDS.md"
        elif doc_type == "acceptance_criteria":
            # Could be in story file or separate
            if workflow_context.story_num is not None:
                file_path = (
                    docs_base / "stories" / f"epic-{workflow_context.epic_num}" /
                    f"story-{workflow_context.epic_num}.{workflow_context.story_num}.md"
                )

        # Load file if path determined
        if file_path and file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                logger.debug(
                    "document_loaded_from_filesystem",
                    doc_type=doc_type,
                    path=str(file_path)
                )
                return content
            except Exception as e:
                logger.error(
                    "document_load_failed",
                    file_path=str(file_path),
                    error=str(e)
                )
                return None

        logger.debug(
            "document_path_not_found",
            doc_type=doc_type,
            file_path=str(file_path) if file_path else None
        )
        return None

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache metrics (hits, misses, size, hit_rate, etc.)
        """
        return self.cache.get_statistics()

    def get_usage_history(self, context_key: Optional[str] = None) -> list:
        """
        Get usage history for this workflow or specific context key.

        Args:
            context_key: Optional filter by context key

        Returns:
            List of usage records
        """
        return self.tracker.get_usage_history(
            workflow_id=self.workflow_context.workflow_id,
            context_key=context_key
        )

    def clear_cache(self) -> None:
        """
        Clear all cached documents.

        Note: This clears the entire cache, affecting all workflows.
        """
        self.cache.clear()
        logger.info("cache_cleared")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AgentContextAPI(workflow_id={self.workflow_context.workflow_id[:8]}..., "
            f"story={self.workflow_context.story_id})"
        )
