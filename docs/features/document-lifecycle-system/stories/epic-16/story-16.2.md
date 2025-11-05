# Story 16.2 (ENHANCED): WorkflowContext Data Model

**Epic:** 16 - Context Persistence Layer
**Story Points:** 3
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Create comprehensive WorkflowContext dataclass that holds all context for workflow execution, including lazy-loaded documents, execution state, decisions, and artifacts. This context object is passed through workflow steps, persists state across executions, and provides a clean API for agents to access project information. The model uses immutable copy-on-write pattern for thread safety and includes JSON serialization for persistence.

---

## Business Value

This story provides the data model foundation for context-aware agent execution:

- **Context Continuity**: Agents maintain context across workflow phases and executions
- **Performance**: Lazy loading prevents loading unused documents
- **Memory Efficiency**: Documents loaded on-demand, cached for reuse
- **Type Safety**: Dataclass provides IDE autocomplete and type checking
- **Immutability**: Copy-on-write pattern prevents accidental state mutation
- **Serialization**: JSON export enables persistence and debugging
- **Extensibility**: Metadata dict allows custom fields without schema changes
- **Audit Trail**: Tracks decisions, artifacts, and state transitions
- **Agent Simplicity**: Clean API reduces agent implementation complexity
- **Testing**: Immutable model enables predictable unit testing

---

## Acceptance Criteria

### Core Identity Fields
- [ ] `workflow_id`: Unique workflow execution ID (UUID)
- [ ] `epic_num`: Current epic number
- [ ] `story_num`: Current story number (optional, None for epic-level)
- [ ] `feature`: Feature name
- [ ] `workflow_name`: Name of workflow being executed

### Cached Documents (Lazy-Loaded)
- [ ] `prd`: PRD content (property, lazy-loaded from file)
- [ ] `architecture`: Architecture content (property, lazy-loaded)
- [ ] `epic_definition`: Epic definition (property, lazy-loaded)
- [ ] `story_definition`: Story content (property, lazy-loaded)
- [ ] `_document_cache`: Internal cache dict for loaded documents
- [ ] Lazy properties only load once per instance
- [ ] Documents loaded via DocumentLifecycleManager

### State Fields
- [ ] `current_phase`: Current workflow phase (string)
- [ ] `phase_history`: List of completed phases with timestamps
- [ ] `decisions`: Dict of decisions made (key: decision_name, value: decision)
- [ ] `artifacts`: List of created artifacts (paths)
- [ ] `errors`: List of errors encountered
- [ ] `status`: Workflow status (running, completed, failed)

### Metadata
- [ ] `created_at`: Creation timestamp (ISO 8601 string)
- [ ] `updated_at`: Last update timestamp (ISO 8601 string)
- [ ] `metadata`: Dict for custom fields (extensible)
- [ ] `tags`: List of tags for categorization

### Operations
- [ ] Lazy loading for document properties (only load when accessed)
- [ ] `to_dict()`: Serialization to JSON-compatible dict
- [ ] `from_dict(data)`: Deserialization from dict (class method)
- [ ] `to_json()`: Serialize to JSON string
- [ ] `from_json(json_str)`: Deserialize from JSON string (class method)
- [ ] Immutable (copy-on-write pattern with frozen dataclass)
- [ ] `copy_with(**changes)`: Create modified copy with updated fields
- [ ] `add_decision(name, value)`: Add decision to context
- [ ] `add_artifact(path)`: Add artifact to context
- [ ] `add_error(error)`: Add error to context
- [ ] `transition_phase(phase)`: Transition to new phase

### Validation
- [ ] Validates workflow_id format (UUID)
- [ ] Validates epic_num is positive integer
- [ ] Validates story_num is positive integer or None
- [ ] Validates timestamps are valid ISO 8601
- [ ] Validates required fields present

---

## Technical Notes

### WorkflowContext Implementation

```python
# gao_dev/core/context/workflow_context.py
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

@dataclass
class PhaseTransition:
    """Record of phase transition."""
    phase: str
    timestamp: str
    duration: Optional[float] = None  # seconds

@dataclass
class WorkflowContext:
    """
    Workflow execution context with lazy-loaded documents.

    Holds all context for workflow execution including documents,
    state, decisions, and artifacts. Immutable with copy-on-write.

    Example:
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            epic_num=12,
            story_num=3,
            feature="document-lifecycle",
            workflow_name="implement_story"
        )

        # Lazy load documents
        prd = context.prd  # Loads on first access

        # Make decisions
        context = context.add_decision("use_sqlite", True)

        # Add artifacts
        context = context.add_artifact("gao_dev/lifecycle/manager.py")

        # Transition phase
        context = context.transition_phase("implementation")

        # Serialize
        json_str = context.to_json()
    """

    # Identity
    workflow_id: str
    epic_num: int
    story_num: Optional[int]
    feature: str
    workflow_name: str

    # State
    current_phase: str = "initialization"
    phase_history: List[PhaseTransition] = field(default_factory=list)
    decisions: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status: str = "running"

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Internal cache for lazy-loaded documents
    _document_cache: Dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        """Validate fields after initialization."""
        # Validate workflow_id is UUID format
        try:
            uuid.UUID(self.workflow_id)
        except ValueError:
            raise ValueError(f"workflow_id must be valid UUID: {self.workflow_id}")

        # Validate epic_num
        if self.epic_num <= 0:
            raise ValueError(f"epic_num must be positive: {self.epic_num}")

        # Validate story_num
        if self.story_num is not None and self.story_num <= 0:
            raise ValueError(f"story_num must be positive or None: {self.story_num}")

    @property
    def prd(self) -> Optional[str]:
        """Get PRD content (lazy-loaded)."""
        if "prd" not in self._document_cache:
            self._document_cache["prd"] = self._load_document("prd")
        return self._document_cache["prd"]

    @property
    def architecture(self) -> Optional[str]:
        """Get architecture content (lazy-loaded)."""
        if "architecture" not in self._document_cache:
            self._document_cache["architecture"] = self._load_document("architecture")
        return self._document_cache["architecture"]

    @property
    def epic_definition(self) -> Optional[str]:
        """Get epic definition (lazy-loaded)."""
        if "epic_definition" not in self._document_cache:
            self._document_cache["epic_definition"] = self._load_document("epic")
        return self._document_cache["epic_definition"]

    @property
    def story_definition(self) -> Optional[str]:
        """Get story definition (lazy-loaded)."""
        if self.story_num is None:
            return None
        if "story_definition" not in self._document_cache:
            self._document_cache["story_definition"] = self._load_document("story")
        return self._document_cache["story_definition"]

    def _load_document(self, doc_type: str) -> Optional[str]:
        """
        Load document from file system.

        Args:
            doc_type: Type of document (prd, architecture, epic, story)

        Returns:
            Document content or None if not found
        """
        # TODO: Integrate with DocumentLifecycleManager
        # For now, return None (placeholder)
        return None

    def add_decision(self, name: str, value: Any) -> "WorkflowContext":
        """
        Add decision to context (immutable).

        Args:
            name: Decision name
            value: Decision value

        Returns:
            New WorkflowContext with decision added
        """
        new_decisions = self.decisions.copy()
        new_decisions[name] = value
        return self.copy_with(decisions=new_decisions)

    def add_artifact(self, path: str) -> "WorkflowContext":
        """
        Add artifact to context (immutable).

        Args:
            path: Artifact file path

        Returns:
            New WorkflowContext with artifact added
        """
        new_artifacts = self.artifacts.copy()
        new_artifacts.append(path)
        return self.copy_with(artifacts=new_artifacts)

    def add_error(self, error: str) -> "WorkflowContext":
        """
        Add error to context (immutable).

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

        # Create transition record
        transition = PhaseTransition(
            phase=self.current_phase,
            timestamp=datetime.now().isoformat(),
            duration=duration
        )

        # Add to history
        new_history = self.phase_history.copy()
        new_history.append(transition)

        return self.copy_with(
            current_phase=phase,
            phase_history=new_history,
            updated_at=datetime.now().isoformat()
        )

    def copy_with(self, **changes) -> "WorkflowContext":
        """
        Create modified copy with updated fields (immutable).

        Args:
            **changes: Fields to update

        Returns:
            New WorkflowContext with changes applied
        """
        # Always update updated_at
        if "updated_at" not in changes:
            changes["updated_at"] = datetime.now().isoformat()

        # Create new instance with changes
        data = asdict(self)
        data.update(changes)
        return WorkflowContext(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to JSON-compatible dict.

        Returns:
            Dict representation (excludes internal cache)
        """
        data = asdict(self)
        # Remove internal cache
        data.pop("_document_cache", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        """
        Deserialize from dict.

        Args:
            data: Dict representation

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

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowContext":
        """
        Deserialize from JSON string.

        Args:
            json_str: JSON string

        Returns:
            WorkflowContext instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @property
    def story_id(self) -> str:
        """Get story ID (e.g., '12.3')."""
        if self.story_num is not None:
            return f"{self.epic_num}.{self.story_num}"
        return f"{self.epic_num}"

    def __repr__(self) -> str:
        """String representation."""
        return f"WorkflowContext(id={self.workflow_id[:8]}..., story={self.story_id}, phase={self.current_phase}, status={self.status})"
```

**Files to Create:**
- `gao_dev/core/context/__init__.py`
- `gao_dev/core/context/workflow_context.py`
- `gao_dev/core/context/models.py`
- `tests/core/context/test_workflow_context.py`
- `tests/core/context/test_workflow_context_serialization.py`

**Dependencies:** Epic 12 (DocumentLifecycleManager - for document loading)

---

## Testing Requirements

### Unit Tests

**Initialization:**
- [ ] Test creating WorkflowContext with required fields
- [ ] Test validates workflow_id is UUID
- [ ] Test validates epic_num is positive
- [ ] Test validates story_num is positive or None
- [ ] Test default values set correctly

**Lazy Loading:**
- [ ] Test PRD property loads on first access
- [ ] Test architecture property loads on first access
- [ ] Test epic_definition property loads on first access
- [ ] Test story_definition property returns None if story_num None
- [ ] Test documents cached after first load
- [ ] Test documents only loaded once

**Immutable Operations:**
- [ ] Test `add_decision()` returns new instance
- [ ] Test `add_decision()` does not modify original
- [ ] Test `add_artifact()` returns new instance
- [ ] Test `add_error()` returns new instance
- [ ] Test `transition_phase()` returns new instance
- [ ] Test `transition_phase()` updates phase_history
- [ ] Test `copy_with()` returns new instance

**Serialization:**
- [ ] Test `to_dict()` returns valid dict
- [ ] Test `to_dict()` excludes internal cache
- [ ] Test `from_dict()` creates instance
- [ ] Test `to_json()` returns valid JSON
- [ ] Test `from_json()` creates instance
- [ ] Test round-trip serialization (to_json -> from_json)

**Properties:**
- [ ] Test `story_id` property returns correct format
- [ ] Test `__repr__()` returns readable string

### Integration Tests
- [ ] Create context, add decisions, serialize, deserialize, verify
- [ ] Create context, transition phases, verify history
- [ ] Create context, add artifacts and errors, verify lists

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods and properties
- [ ] API documentation with usage examples
- [ ] Lazy loading behavior documentation
- [ ] Immutability pattern documentation
- [ ] Serialization format documentation
- [ ] Integration guide with DocumentLifecycleManager
- [ ] Example usage patterns for agents
- [ ] Testing guide for context-dependent code

---

## Implementation Details

### Development Approach

**Phase 1: Core Data Model**
1. Define WorkflowContext dataclass with all fields
2. Add validation in __post_init__
3. Add basic operations (add_decision, add_artifact)
4. Write unit tests for core functionality

**Phase 2: Lazy Loading**
1. Implement lazy-loaded properties (prd, architecture, etc.)
2. Add document caching
3. Test lazy loading behavior

**Phase 3: Serialization**
1. Implement to_dict/from_dict
2. Implement to_json/from_json
3. Test round-trip serialization
4. Handle edge cases (None values, nested objects)

### Quality Gates
- [ ] All unit tests pass with >80% coverage
- [ ] Serialization round-trip tested
- [ ] Immutability verified (original unchanged after operations)
- [ ] Validation catches invalid inputs
- [ ] Documentation complete with examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All fields defined with proper types
- [ ] Lazy loading implemented for documents
- [ ] Immutable operations working (copy-on-write)
- [ ] Serialization working (JSON round-trip)
- [ ] Validation working for all fields
- [ ] Tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete with examples
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-16): implement Story 16.2 - WorkflowContext Data Model

  - Create WorkflowContext dataclass with all execution context
  - Implement lazy-loaded document properties (prd, architecture, epic, story)
  - Add immutable operations (add_decision, add_artifact, transition_phase)
  - Implement JSON serialization (to_dict, from_dict, to_json, from_json)
  - Add field validation (workflow_id UUID, positive numbers)
  - Support copy-on-write pattern for thread safety
  - Add comprehensive unit tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
