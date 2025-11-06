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
from typing import Optional, Dict, Any, List

from gao_dev.core.context.models import PhaseTransition


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
    _document_cache: Dict[str, str] = field(default_factory=dict, repr=False)

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
            raise ValueError(f"Timestamps must be valid ISO 8601 format") from e

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
        Load document from file system.

        This is a placeholder implementation. In production, this should
        integrate with DocumentLifecycleManager (Epic 12) to load documents
        from the proper location based on feature, epic, and story numbers.

        Args:
            doc_type: Type of document (prd, architecture, epic, story)

        Returns:
            Document content or None if not found
        """
        # TODO: Integrate with DocumentLifecycleManager (Epic 12)
        # For now, return None (placeholder)
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
        # Preserve document cache from original instance
        cache = data.pop("_document_cache", {})
        data.update(changes)
        result = WorkflowContext(**data)
        # Copy document cache to new instance (avoid reloading)
        result._document_cache = cache.copy()
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
