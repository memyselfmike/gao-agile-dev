"""
WorkflowContext data model for workflow execution.

This module provides the WorkflowContext dataclass that holds all context
for workflow execution including documents, state, decisions, and artifacts.
Uses immutable copy-on-write pattern for thread safety.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import structlog

from gao_dev.core.context.models import PhaseTransition
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import DocumentType

logger = structlog.get_logger(__name__)


@dataclass
class WorkflowContext:
    """
    Workflow execution context with lazy-loaded documents.

    Holds all context for workflow execution including documents,
    state, decisions, and artifacts. Immutable with copy-on-write.

    This context object is passed through workflow steps, persists state
    across executions, and provides a clean API for agents to access
    project information.

    Attributes:
        workflow_id: Unique workflow execution ID (UUID string)
        epic_num: Current epic number (positive integer)
        story_num: Current story number (positive integer or None for epic-level)
        feature: Feature name
        workflow_name: Name of workflow being executed
        current_phase: Current workflow phase
        phase_history: List of completed phases with timestamps
        decisions: Dict of decisions made (key: decision_name, value: decision)
        artifacts: List of created artifacts (file paths)
        errors: List of errors encountered
        status: Workflow status (running, completed, failed)
        created_at: Creation timestamp (ISO 8601 string)
        updated_at: Last update timestamp (ISO 8601 string)
        metadata: Dict for custom fields (extensible)
        tags: List of tags for categorization

    Example:
        >>> context = WorkflowContext(
        ...     workflow_id=str(uuid.uuid4()),
        ...     epic_num=12,
        ...     story_num=3,
        ...     feature="document-lifecycle",
        ...     workflow_name="implement_story"
        ... )
        >>>
        >>> # Lazy load documents
        >>> prd = context.prd  # Loads on first access
        >>>
        >>> # Make decisions
        >>> context = context.add_decision("use_sqlite", True)
        >>>
        >>> # Add artifacts
        >>> context = context.add_artifact("gao_dev/lifecycle/manager.py")
        >>>
        >>> # Transition phase
        >>> context = context.transition_phase("implementation")
        >>>
        >>> # Serialize
        >>> json_str = context.to_json()
    """

    # Identity fields (required)
    workflow_id: str
    epic_num: int
    story_num: Optional[int]
    feature: str
    workflow_name: str

    # State fields (with defaults)
    current_phase: str = "initialization"
    phase_history: List[PhaseTransition] = field(default_factory=list)
    decisions: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status: str = "running"

    # Metadata fields
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Internal cache for lazy-loaded documents (not serialized)
    _document_cache: Dict[str, Optional[str]] = field(default_factory=dict, repr=False)

    # Optional custom document loader (not serialized)
    _document_loader: Optional[Callable[[str], Optional[str]]] = field(
        default=None, repr=False
    )

    def __post_init__(self) -> None:
        """
        Validate fields after initialization.

        Raises:
            ValueError: If workflow_id is not valid UUID
            ValueError: If epic_num is not positive
            ValueError: If story_num is not positive or None
        """
        # Validate workflow_id is UUID format
        try:
            uuid.UUID(self.workflow_id)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"workflow_id must be valid UUID: {self.workflow_id}") from e

        # Validate epic_num
        if not isinstance(self.epic_num, int) or self.epic_num <= 0:
            raise ValueError(f"epic_num must be positive integer: {self.epic_num}")

        # Validate story_num
        if self.story_num is not None:
            if not isinstance(self.story_num, int) or self.story_num <= 0:
                raise ValueError(
                    f"story_num must be positive integer or None: {self.story_num}"
                )

        # Validate timestamps are valid ISO 8601
        try:
            datetime.fromisoformat(self.created_at)
            datetime.fromisoformat(self.updated_at)
        except (ValueError, AttributeError) as e:
            raise ValueError("Timestamps must be valid ISO 8601 format") from e

    @property
    def prd(self) -> Optional[str]:
        """
        Get PRD content (lazy-loaded).

        Loads PRD document from file system on first access, then caches
        for subsequent accesses. Returns None if document not found.

        Returns:
            PRD content or None if not found
        """
        if "prd" not in self._document_cache:
            self._document_cache["prd"] = self._load_document("prd")
        return self._document_cache["prd"]

    @property
    def architecture(self) -> Optional[str]:
        """
        Get architecture content (lazy-loaded).

        Loads architecture document from file system on first access,
        then caches for subsequent accesses. Returns None if document not found.

        Returns:
            Architecture content or None if not found
        """
        if "architecture" not in self._document_cache:
            self._document_cache["architecture"] = self._load_document("architecture")
        return self._document_cache["architecture"]

    @property
    def epic_definition(self) -> Optional[str]:
        """
        Get epic definition (lazy-loaded).

        Loads epic document from file system on first access, then caches
        for subsequent accesses. Returns None if document not found.

        Returns:
            Epic definition content or None if not found
        """
        if "epic_definition" not in self._document_cache:
            self._document_cache["epic_definition"] = self._load_document("epic")
        return self._document_cache["epic_definition"]

    @property
    def story_definition(self) -> Optional[str]:
        """
        Get story definition (lazy-loaded).

        Loads story document from file system on first access, then caches
        for subsequent accesses. Returns None if story_num is None or
        document not found.

        Returns:
            Story definition content or None if story_num is None or not found
        """
        if self.story_num is None:
            return None
        if "story_definition" not in self._document_cache:
            self._document_cache["story_definition"] = self._load_document("story")
        return self._document_cache["story_definition"]

    def _load_document(self, doc_type: str) -> Optional[str]:
        """
        Load document from file system using DocumentLifecycleManager.

        This method integrates with DocumentLifecycleManager (Epic 12) to load
        documents from the registry. If a custom document loader is provided,
        it will be used instead. Falls back to file-based loading if registry
        access fails.

        Args:
            doc_type: Type of document (prd, architecture, epic, story)

        Returns:
            Document content or None if not found

        Example:
            >>> context = WorkflowContext(...)
            >>> prd_content = context._load_document("prd")
        """
        # Use custom loader if provided
        if self._document_loader is not None:
            try:
                return self._document_loader(doc_type)
            except Exception as e:
                logger.warning(
                    "custom_document_loader_failed",
                    doc_type=doc_type,
                    error=str(e)
                )
                # Fall through to default loading

        # Map doc_type string to DocumentType enum
        doc_type_map = {
            "prd": DocumentType.PRD,
            "architecture": DocumentType.ARCHITECTURE,
            "epic": DocumentType.EPIC,
            "epic_definition": DocumentType.EPIC,
            "story": DocumentType.STORY,
            "story_definition": DocumentType.STORY,
        }

        document_type = doc_type_map.get(doc_type)
        if document_type is None:
            logger.warning("unknown_document_type", doc_type=doc_type)
            return None

        try:
            # Try loading from DocumentLifecycleManager
            content = self._load_from_lifecycle_manager(document_type)
            if content is not None:
                return content

            # Fall back to file-based loading
            return self._load_from_filesystem(doc_type)

        except Exception as e:
            logger.error(
                "document_load_failed",
                doc_type=doc_type,
                feature=self.feature,
                epic=self.epic_num,
                story=self.story_num,
                error=str(e)
            )
            return None

    def _load_from_lifecycle_manager(
        self,
        document_type: DocumentType
    ) -> Optional[str]:
        """
        Load document from DocumentLifecycleManager registry.

        Args:
            document_type: DocumentType enum value

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
                feature=self.feature
            )

            # Close registry connection
            registry.close()

            if document is None:
                logger.debug(
                    "document_not_found_in_registry",
                    doc_type=document_type.value,
                    feature=self.feature
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

    def _load_from_filesystem(self, doc_type: str) -> Optional[str]:
        """
        Load document directly from filesystem (fallback).

        Uses standard docs/features directory structure.

        Args:
            doc_type: Type of document (string)

        Returns:
            Document content or None if not found
        """
        docs_base = Path.cwd() / "docs" / "features" / self.feature

        file_path: Optional[Path] = None

        if doc_type in ("prd",):
            file_path = docs_base / "PRD.md"
        elif doc_type in ("architecture",):
            file_path = docs_base / "ARCHITECTURE.md"
        elif doc_type in ("epic", "epic_definition"):
            file_path = docs_base / "epics" / f"epic-{self.epic_num}.md"
        elif doc_type in ("story", "story_definition"):
            if self.story_num is not None:
                file_path = (
                    docs_base / "stories" / f"epic-{self.epic_num}" /
                    f"story-{self.epic_num}.{self.story_num}.md"
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
                    "filesystem_read_failed",
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

    def add_decision(self, name: str, value: Any) -> "WorkflowContext":
        """
        Add decision to context (immutable).

        Creates a new WorkflowContext instance with the decision added.
        Does not modify the original instance.

        Args:
            name: Decision name/key
            value: Decision value (any JSON-serializable value)

        Returns:
            New WorkflowContext with decision added
        """
        new_decisions = self.decisions.copy()
        new_decisions[name] = value
        return self.copy_with(decisions=new_decisions)

    def add_artifact(self, path: str) -> "WorkflowContext":
        """
        Add artifact to context (immutable).

        Creates a new WorkflowContext instance with the artifact added.
        Does not modify the original instance.

        Args:
            path: Artifact file path (relative or absolute)

        Returns:
            New WorkflowContext with artifact added
        """
        new_artifacts = self.artifacts.copy()
        new_artifacts.append(path)
        return self.copy_with(artifacts=new_artifacts)

    def add_error(self, error: str) -> "WorkflowContext":
        """
        Add error to context (immutable).

        Creates a new WorkflowContext instance with the error added.
        Does not modify the original instance.

        Args:
            error: Error message

        Returns:
            New WorkflowContext with error added
        """
        new_errors = self.errors.copy()
        new_errors.append(error)
        return self.copy_with(errors=new_errors)

    def transition_phase(self, phase: str) -> "WorkflowContext":
        """
        Transition to new phase (immutable).

        Creates a new WorkflowContext instance in the new phase. Calculates
        duration of previous phase and adds to phase_history. Does not
        modify the original instance.

        Args:
            phase: New phase name

        Returns:
            New WorkflowContext in new phase
        """
        # Calculate duration of previous phase
        duration = None
        if self.phase_history:
            last_transition = self.phase_history[-1]
            last_time = datetime.fromisoformat(last_transition.timestamp)
            duration = (datetime.now() - last_time).total_seconds()

        # Create transition record for current phase
        transition = PhaseTransition(
            phase=self.current_phase,
            timestamp=datetime.now().isoformat(),
            duration=duration,
        )

        # Add to history
        new_history = self.phase_history.copy()
        new_history.append(transition)

        return self.copy_with(
            current_phase=phase,
            phase_history=new_history,
            updated_at=datetime.now().isoformat(),
        )

    def copy_with(self, **changes: Any) -> "WorkflowContext":
        """
        Create modified copy with updated fields (immutable).

        Creates a new WorkflowContext instance with the specified fields
        updated. Automatically updates updated_at timestamp unless explicitly
        provided. Does not modify the original instance.

        Args:
            **changes: Fields to update (any WorkflowContext field)

        Returns:
            New WorkflowContext with changes applied
        """
        # Always update updated_at unless explicitly provided
        if "updated_at" not in changes:
            changes["updated_at"] = datetime.now().isoformat()

        # Create new instance with changes
        data = asdict(self)
        # Preserve document cache and loader from original instance
        cache = data.pop("_document_cache", {})
        loader = data.pop("_document_loader", None)
        data.update(changes)
        result = WorkflowContext(**data)
        # Copy document cache to new instance (avoid reloading)
        result._document_cache = cache.copy()
        # Preserve custom document loader
        result._document_loader = loader
        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to JSON-compatible dict.

        Converts WorkflowContext to a dictionary that can be serialized
        to JSON. Excludes internal cache (_document_cache) from output.
        PhaseTransition objects are converted to dicts.

        Returns:
            Dict representation (excludes internal cache)
        """
        data = asdict(self)
        # Remove internal cache (not for serialization)
        data.pop("_document_cache", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        """
        Deserialize from dict.

        Creates WorkflowContext instance from dictionary representation.
        Converts phase_history dicts back to PhaseTransition objects.

        Args:
            data: Dict representation (from to_dict())

        Returns:
            WorkflowContext instance
        """
        # Convert phase_history dicts to PhaseTransition objects
        if "phase_history" in data:
            data["phase_history"] = [
                PhaseTransition(**t) if isinstance(t, dict) else t
                for t in data["phase_history"]
            ]
        return cls(**data)

    def to_json(self) -> str:
        """
        Serialize to JSON string.

        Converts WorkflowContext to formatted JSON string with 2-space
        indentation. Uses to_dict() for conversion.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowContext":
        """
        Deserialize from JSON string.

        Creates WorkflowContext instance from JSON string representation.
        Uses from_dict() for conversion.

        Args:
            json_str: JSON string (from to_json())

        Returns:
            WorkflowContext instance

        Raises:
            json.JSONDecodeError: If json_str is not valid JSON
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @property
    def story_id(self) -> str:
        """
        Get story ID in format 'epic.story'.

        Returns story ID string like '12.3' for stories or '12' for
        epic-level context (when story_num is None).

        Returns:
            Story ID string (e.g., '12.3' or '12')
        """
        if self.story_num is not None:
            return f"{self.epic_num}.{self.story_num}"
        return f"{self.epic_num}"

    def __repr__(self) -> str:
        """
        String representation of WorkflowContext.

        Returns compact representation showing key identifying information.

        Returns:
            String representation
        """
        return (
            f"WorkflowContext(id={self.workflow_id[:8]}..., "
            f"story={self.story_id}, phase={self.current_phase}, "
            f"status={self.status})"
        )
