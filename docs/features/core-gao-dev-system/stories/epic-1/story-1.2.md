# Story 1.2: Create Value Objects

**Epic**: Epic 1 - Foundation
**Story Points**: 3
**Priority**: P0 (Critical)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** immutable value objects for domain concepts
**So that** we have type-safe, validated representations of key business entities

---

## Description

Create value objects for core domain concepts such as ProjectPath, WorkflowIdentifier, StoryIdentifier, and AgentCapability. Value objects are immutable objects that represent concepts by their values rather than identity.

These value objects will be used throughout the codebase to ensure type safety and encapsulate validation logic.

---

## Acceptance Criteria

### Value Objects Created

- [ ] **ProjectPath** value object created in `gao_dev/core/models/project.py`
  - Properties: root (Path), docs, stories, prd, architecture, epics
  - Validation: root must exist and be absolute
  - Immutable: frozen dataclass
  - Methods: to_dict(), __str__()

- [ ] **StoryIdentifier** value object created in `gao_dev/core/models/story.py`
  - Properties: epic (int), story (int)
  - Validation: epic >= 1, story >= 1
  - Methods: to_string() → "1.1", to_path() → "epic-1/story-1.1.md"
  - Comparison: __eq__, __hash__ for use in sets/dicts

- [ ] **WorkflowIdentifier** value object created in `gao_dev/core/models/workflow.py`
  - Properties: name (str), phase (int), version (Optional[str])
  - Validation: name not empty, phase 0-4
  - Methods: to_string(), __str__()

- [ ] **AgentCapability** value object created in `gao_dev/core/models/agent.py`
  - Properties: capability_type (str), description (str), required_tools (List[str])
  - Enumeration of common capabilities (PLANNING, IMPLEMENTATION, TESTING, etc.)
  - Immutable

- [ ] **ComplexityLevel** value object created in `gao_dev/core/models/workflow.py`
  - Properties: level (int), description (str), estimated_stories (range)
  - Factory methods: from_scale_level(), from_story_count()
  - Comparison operators for level ordering

### Code Quality

- [ ] All value objects are immutable (frozen dataclass or similar)
- [ ] All value objects have validation in __post_init__
- [ ] All value objects have __eq__ and __hash__ methods
- [ ] All value objects have __str__ and __repr__ methods
- [ ] Type hints on all properties and methods

### Testing

- [ ] **ProjectPath** tests:
  - Valid path creation
  - Invalid path raises ValueError
  - Computed properties return correct paths
  - Immutability enforced

- [ ] **StoryIdentifier** tests:
  - Valid identifier creation
  - Invalid values raise ValueError
  - to_string() format correct
  - to_path() format correct
  - Equality and hashing work correctly

- [ ] **WorkflowIdentifier** tests:
  - Valid identifier creation
  - Validation works
  - String representation correct

- [ ] **AgentCapability** tests:
  - Common capabilities defined
  - Immutability enforced
  - Proper representation

- [ ] **ComplexityLevel** tests:
  - Factory methods work
  - Comparison operators work
  - Validation works

### Documentation

- [ ] Each value object has comprehensive docstring
- [ ] Example usage provided for each value object
- [ ] Validation rules documented

---

## Technical Details

### Example Value Object (StoryIdentifier)

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Self

@dataclass(frozen=True)
class StoryIdentifier:
    """
    Immutable identifier for a user story.

    Stories are identified by their epic and story numbers.
    Example: Epic 1, Story 3 → StoryIdentifier(1, 3)

    Attributes:
        epic: Epic number (>= 1)
        story: Story number within epic (>= 1)
    """

    epic: int
    story: int

    def __post_init__(self):
        """Validate story identifier."""
        if self.epic < 1:
            raise ValueError(f"Epic must be >= 1, got {self.epic}")
        if self.story < 1:
            raise ValueError(f"Story must be >= 1, got {self.story}")

    def to_string(self) -> str:
        """
        Convert to string format "E.S".

        Returns:
            str: Story identifier as "1.1", "2.3", etc.
        """
        return f"{self.epic}.{self.story}"

    def to_path(self) -> Path:
        """
        Convert to file path.

        Returns:
            Path: Relative path like "epic-1/story-1.1.md"
        """
        return Path(f"epic-{self.epic}") / f"story-{self.epic}.{self.story}.md"

    @classmethod
    def from_string(cls, s: str) -> Self:
        """
        Parse from string format "E.S".

        Args:
            s: String like "1.1" or "2.3"

        Returns:
            StoryIdentifier instance

        Raises:
            ValueError: If string format invalid
        """
        try:
            epic_str, story_str = s.split('.')
            return cls(epic=int(epic_str), story=int(story_str))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid story identifier: {s}") from e

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"StoryIdentifier({self.epic}, {self.story})"
```

### ProjectPath Computed Properties

```python
@dataclass(frozen=True)
class ProjectPath:
    """Encapsulates all paths for a GAO-Dev project."""

    root: Path

    def __post_init__(self):
        """Validate root path."""
        if not self.root.is_absolute():
            raise ValueError("Project root must be absolute path")
        if not self.root.exists():
            raise ValueError(f"Project root does not exist: {self.root}")

    @property
    def docs(self) -> Path:
        """Documentation directory."""
        return self.root / "docs"

    @property
    def stories(self) -> Path:
        """Stories directory."""
        return self.docs / "stories"

    @property
    def prd(self) -> Path:
        """PRD file path."""
        return self.docs / "PRD.md"

    # ... more computed paths
```

---

## Implementation Notes

### Implementation Order

1. Create models directory: `gao_dev/core/models/`
2. Implement StoryIdentifier (simplest)
3. Implement WorkflowIdentifier
4. Implement ProjectPath (with validation)
5. Implement AgentCapability
6. Implement ComplexityLevel
7. Create __init__.py with exports

### Design Decisions

- **Immutability**: Use frozen dataclasses for value objects
- **Validation**: All validation in __post_init__
- **Equality**: Dataclasses provide __eq__ and __hash__ automatically
- **String Conversion**: Implement __str__ and __repr__ for debugging

---

## Testing

### Test Coverage Target

- 100% line coverage (value objects are critical)
- Test all validation rules
- Test all conversion methods
- Test equality and hashing

### Test Examples

```python
def test_story_identifier_valid():
    story_id = StoryIdentifier(1, 1)
    assert story_id.epic == 1
    assert story_id.story == 1
    assert story_id.to_string() == "1.1"

def test_story_identifier_invalid_epic():
    with pytest.raises(ValueError, match="Epic must be >= 1"):
        StoryIdentifier(0, 1)

def test_story_identifier_equality():
    id1 = StoryIdentifier(1, 1)
    id2 = StoryIdentifier(1, 1)
    id3 = StoryIdentifier(1, 2)

    assert id1 == id2
    assert id1 != id3
    assert hash(id1) == hash(id2)

def test_story_identifier_immutable():
    story_id = StoryIdentifier(1, 1)
    with pytest.raises(AttributeError):
        story_id.epic = 2  # Should fail (frozen)
```

---

## Dependencies

### Depends On

- Story 1.1: Define Core Interfaces (minimal dependency, just for consistency)

### Blocks

- Story 1.3, 1.4: Base classes will use these value objects
- Epic 2: Extracted components will use value objects
- All future stories: Value objects used throughout

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All value objects implemented
- [ ] 100% test coverage for all value objects
- [ ] All tests passing
- [ ] Type hints complete (mypy passes)
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Merged to feature branch

---

## Notes

- Value objects should never change after creation (immutable)
- Validation should be comprehensive but reasonable
- Consider performance for frequently created value objects
- Keep value objects simple (no complex business logic)

---

## Related

- **Epic**: Epic 1 - Foundation
- **Previous Story**: Story 1.1 - Define Core Interfaces
- **Next Story**: Story 1.3 - Implement Base Agent Class
