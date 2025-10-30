# Story 5.1: Create IMethodology Interface

**Epic**: Epic 5 - Methodology Abstraction
**Story Points**: 3
**Priority**: P2 (Medium)
**Status**: Ready

---

## User Story

**As a** core developer
**I want** a methodology interface that abstracts development process logic
**So that** GAO-Dev can support multiple methodologies (BMAD, Scrum, Kanban, etc.) interchangeably

---

## Description

Create the `IMethodology` interface that defines the contract for all development methodologies in GAO-Dev. This interface will abstract complexity assessment, workflow selection, and agent recommendations - currently hardcoded for BMAD Method.

**Current State**: BMAD logic is tightly coupled throughout core (brian_orchestrator.py, workflow selection, scale levels everywhere).

**Target State**: Clean interface in `gao_dev/core/interfaces/methodology.py` that any methodology can implement.

---

## Acceptance Criteria

### Interface Definition

- [ ] **File created**: `gao_dev/core/interfaces/methodology.py`
- [ ] **IMethodology interface** defined with all required methods
- [ ] **Size**: < 200 lines (interface + documentation)
- [ ] **Type hints**: Complete typing for all methods
- [ ] **Documentation**: Comprehensive docstrings with examples

### Core Methods

- [ ] **assess_complexity(prompt: str, context: Optional[Dict]) -> ComplexityAssessment**
  - Analyzes user prompt to determine project complexity
  - Returns structured assessment (not BMAD-specific)
  - Must be methodology-agnostic
  - Context can include project history, files, etc.

- [ ] **build_workflow_sequence(assessment: ComplexityAssessment) -> WorkflowSequence**
  - Takes complexity assessment
  - Returns ordered sequence of workflows to execute
  - Each methodology decides its own workflow strategy
  - Returns generic WorkflowSequence, not BMAD-specific

- [ ] **get_recommended_agents(task: str, context: Optional[Dict]) -> List[str]**
  - Recommends which agents to use for a task
  - Returns list of agent names
  - Methodology-specific agent selection logic
  - Context can include workflow phase, project type, etc.

- [ ] **validate_config(config: Dict) -> ValidationResult**
  - Validates methodology-specific configuration
  - Returns ValidationResult with errors/warnings
  - Each methodology has different config requirements

### Properties

- [ ] **name: str** (property)
  - Unique methodology identifier (e.g., "bmad", "scrum", "kanban")
  - Read-only property

- [ ] **description: str** (property)
  - Human-readable methodology description
  - Read-only property

- [ ] **version: str** (property)
  - Methodology version (semantic versioning)
  - Read-only property

- [ ] **supports_scale_levels: bool** (property)
  - Whether methodology uses scale levels concept
  - BMAD uses scale levels (0-4), but other methodologies may not

### Supporting Models

- [ ] **ComplexityAssessment dataclass** created:
  - complexity_level: ComplexityLevel (enum)
  - project_type: Optional[ProjectType]
  - estimated_stories: Optional[int]
  - estimated_epics: Optional[int]
  - confidence: float (0.0-1.0)
  - reasoning: str (explanation of assessment)
  - metadata: Dict[str, Any] (methodology-specific data)

- [ ] **ComplexityLevel enum** created (generic, not BMAD-specific):
  - TRIVIAL = "trivial"  # Single file change, minutes
  - SMALL = "small"      # Few files, hours
  - MEDIUM = "medium"    # Multiple components, days
  - LARGE = "large"      # Complex feature, weeks
  - XLARGE = "xlarge"    # Greenfield app, months

- [ ] **WorkflowSequence dataclass** created:
  - workflows: List[WorkflowStep]
  - total_phases: int
  - estimated_duration: Optional[timedelta]
  - can_parallelize: bool
  - metadata: Dict[str, Any]

- [ ] **WorkflowStep dataclass** created:
  - workflow_name: str
  - phase: str
  - required: bool
  - depends_on: List[str]
  - parallel_group: Optional[int]

### Testing

- [ ] Unit tests for interface (mock implementation) - 80%+ coverage
- [ ] Test ComplexityAssessment dataclass validation
- [ ] Test WorkflowSequence construction
- [ ] Test interface method signatures (type hints)
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

**1. Create IMethodology Interface**:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import timedelta

# Supporting Enums
class ComplexityLevel(Enum):
    """Generic complexity levels (not BMAD-specific)."""
    TRIVIAL = "trivial"    # Chore, typo fix, minutes
    SMALL = "small"        # Bug fix, small feature, hours
    MEDIUM = "medium"      # Feature with tests, days
    LARGE = "large"        # Complex feature, weeks
    XLARGE = "xlarge"      # Greenfield application, months

class ProjectType(Enum):
    """Types of software projects."""
    WEB_APP = "web_app"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    DATA_PIPELINE = "data_pipeline"
    ML_MODEL = "ml_model"
    UNKNOWN = "unknown"

# Supporting Models
@dataclass
class ComplexityAssessment:
    """Result of complexity analysis.

    Attributes:
        complexity_level: Overall complexity (trivial to xlarge)
        project_type: Type of project being built
        estimated_stories: Approximate number of user stories
        estimated_epics: Approximate number of epics
        confidence: Confidence in assessment (0.0-1.0)
        reasoning: Human-readable explanation
        metadata: Methodology-specific additional data
    """
    complexity_level: ComplexityLevel
    project_type: Optional[ProjectType] = None
    estimated_stories: Optional[int] = None
    estimated_epics: Optional[int] = None
    confidence: float = 0.5
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate assessment."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.estimated_stories and self.estimated_stories < 0:
            raise ValueError("Estimated stories must be >= 0")

@dataclass
class WorkflowStep:
    """A single step in workflow sequence.

    Attributes:
        workflow_name: Name of workflow to execute
        phase: Which phase this belongs to
        required: Whether this step is mandatory
        depends_on: List of workflow names this depends on
        parallel_group: Group number for parallel execution
    """
    workflow_name: str
    phase: str
    required: bool = True
    depends_on: List[str] = field(default_factory=list)
    parallel_group: Optional[int] = None

@dataclass
class WorkflowSequence:
    """Ordered sequence of workflows to execute.

    Attributes:
        workflows: List of workflow steps in execution order
        total_phases: Number of distinct phases
        estimated_duration: Expected time to complete
        can_parallelize: Whether workflows can run in parallel
        metadata: Methodology-specific additional data
    """
    workflows: List[WorkflowStep] = field(default_factory=list)
    total_phases: int = 0
    estimated_duration: Optional[timedelta] = None
    can_parallelize: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result of configuration validation.

    Attributes:
        valid: Whether configuration is valid
        errors: List of error messages
        warnings: List of warning messages
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

# Main Interface
class IMethodology(ABC):
    """Interface for development methodologies.

    Methodologies define how GAO-Dev analyzes complexity, selects workflows,
    and recommends agents. This abstraction allows supporting BMAD, Scrum,
    Kanban, or custom methodologies.

    Example:
        ```python
        class MyMethodology(IMethodology):
            @property
            def name(self) -> str:
                return "my-methodology"

            async def assess_complexity(
                self,
                prompt: str,
                context: Optional[Dict[str, Any]] = None
            ) -> ComplexityAssessment:
                # Analyze prompt, return assessment
                return ComplexityAssessment(
                    complexity_level=ComplexityLevel.MEDIUM,
                    reasoning="Detected API project with auth"
                )

            def build_workflow_sequence(
                self,
                assessment: ComplexityAssessment
            ) -> WorkflowSequence:
                # Return workflows for this complexity
                return WorkflowSequence(
                    workflows=[
                        WorkflowStep("create-prd", "planning"),
                        WorkflowStep("create-architecture", "design")
                    ]
                )
        ```

    Attributes:
        name: Unique methodology identifier
        description: Human-readable description
        version: Methodology version
        supports_scale_levels: Whether uses scale levels concept
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique methodology identifier (e.g., 'bmad', 'scrum').

        Returns:
            Lowercase kebab-case name
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable methodology description.

        Returns:
            Description of methodology approach
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Methodology version (semantic versioning).

        Returns:
            Version string (e.g., "1.0.0")
        """
        pass

    @property
    def supports_scale_levels(self) -> bool:
        """Whether methodology uses scale levels.

        BMAD uses scale levels (0-4), but other methodologies may not.
        Default: False

        Returns:
            True if methodology uses scale levels
        """
        return False

    @abstractmethod
    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """Analyze prompt to determine project complexity.

        Args:
            prompt: User's initial request
            context: Optional context (project history, files, etc.)

        Returns:
            ComplexityAssessment with level, type, estimates

        Example:
            ```python
            assessment = await methodology.assess_complexity(
                "Build a todo app with auth and real-time sync",
                context={"project_type": "web_app"}
            )
            print(assessment.complexity_level)  # ComplexityLevel.MEDIUM
            ```
        """
        pass

    @abstractmethod
    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        """Build workflow sequence based on complexity assessment.

        Args:
            assessment: Complexity assessment from assess_complexity()

        Returns:
            WorkflowSequence with ordered steps

        Example:
            ```python
            sequence = methodology.build_workflow_sequence(assessment)
            for step in sequence.workflows:
                print(f"{step.phase}: {step.workflow_name}")
            ```
        """
        pass

    @abstractmethod
    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents for a specific task.

        Args:
            task: Task description or type
            context: Optional context (workflow phase, project type, etc.)

        Returns:
            List of agent names

        Example:
            ```python
            agents = methodology.get_recommended_agents(
                "Create architecture document",
                context={"phase": "design"}
            )
            # Returns: ["Winston", "Sally"]
            ```
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate methodology-specific configuration.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult with errors/warnings

        Example:
            ```python
            result = methodology.validate_config({
                "scale_level": 3,
                "project_type": "web_app"
            })
            if not result.valid:
                print(f"Errors: {result.errors}")
            ```
        """
        pass
```

---

## Dependencies

- **Depends On**: Epic 1 complete (interfaces established)
- **Blocks**:
  - Story 5.2 (BMAD implementation needs interface)
  - Story 5.3 (Registry needs interface)
  - Story 5.4 (Core needs interface)

---

## Definition of Done

- [ ] IMethodology interface defined with all methods
- [ ] ComplexityAssessment, WorkflowSequence, WorkflowStep models created
- [ ] ComplexityLevel enum (generic, not BMAD-specific)
- [ ] All methods have comprehensive docstrings with examples
- [ ] Complete type hints (mypy passes strict)
- [ ] 80%+ test coverage (mock implementation tests)
- [ ] All existing tests pass (100%)
- [ ] Code review approved
- [ ] Committed to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/core/interfaces/methodology.py` - IMethodology interface
2. `gao_dev/core/models/methodology.py` - Supporting models
3. `tests/core/interfaces/test_methodology.py` - Interface tests

---

## Files to Modify

1. `gao_dev/core/interfaces/__init__.py` - Export IMethodology
2. `gao_dev/core/models/__init__.py` - Export models

---

## Related

- **Epic**: Epic 5 - Methodology Abstraction
- **Next Story**: Story 5.2 - Extract BMAD Methodology Implementation
- **Pattern**: Strategy pattern (from Epic 3)

---

## Notes

- This is pure interface design - no BMAD logic here
- ComplexityLevel is generic (not tied to BMAD scale levels)
- Interface must be flexible enough for any methodology
- Focus on clean abstractions, not specific implementations
