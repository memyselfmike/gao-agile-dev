"""Methodology data models.

This module provides data models for methodology-related concepts including
complexity assessment, workflow sequences, and validation results.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class ComplexityLevel(Enum):
    """Generic complexity levels for projects.

    These are methodology-agnostic complexity levels. Individual methodologies
    (like BMAD with scale levels 0-4) map their specific levels to these.

    Levels:
        TRIVIAL: Minutes - Simple chore, typo fix, config change
        SMALL: Hours - Bug fix, single file change
        MEDIUM: Days - Feature with tests, multiple files
        LARGE: Weeks - Complex feature, multiple components
        XLARGE: Months - Greenfield application, full system
    """

    TRIVIAL = "trivial"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


class ProjectType(Enum):
    """Types of software projects.

    Used by methodologies to understand project context and tailor
    workflow selection and agent recommendations.
    """

    WEB_APP = "web_app"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    DATA_PIPELINE = "data_pipeline"
    ML_MODEL = "ml_model"
    UNKNOWN = "unknown"


@dataclass
class ComplexityAssessment:
    """Result of complexity analysis.

    Methodologies analyze user prompts to determine project complexity,
    type, and scope. This assessment drives workflow selection.

    Attributes:
        complexity_level: Overall complexity (trivial to xlarge)
        project_type: Type of project being built
        estimated_stories: Approximate number of user stories
        estimated_epics: Approximate number of epics
        confidence: Confidence in assessment (0.0-1.0)
        reasoning: Human-readable explanation of assessment
        metadata: Methodology-specific additional data

    Example:
        ```python
        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM,
            project_type=ProjectType.WEB_APP,
            estimated_stories=8,
            estimated_epics=2,
            confidence=0.85,
            reasoning="Detected web app with authentication",
            metadata={"scale_level": 2}  # BMAD-specific
        )
        ```
    """

    complexity_level: ComplexityLevel
    project_type: Optional[ProjectType] = None
    estimated_stories: Optional[int] = None
    estimated_epics: Optional[int] = None
    confidence: float = 0.5
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate assessment after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        if self.estimated_stories is not None and self.estimated_stories < 0:
            raise ValueError(
                f"Estimated stories must be >= 0, got {self.estimated_stories}"
            )
        if self.estimated_epics is not None and self.estimated_epics < 0:
            raise ValueError(
                f"Estimated epics must be >= 0, got {self.estimated_epics}"
            )


@dataclass
class WorkflowStep:
    """A single step in a workflow sequence.

    Represents one workflow to execute as part of the overall development
    process. Steps can have dependencies and parallel groups.

    Attributes:
        workflow_name: Name of workflow to execute
        phase: Which phase this belongs to (e.g., "planning", "implementation")
        required: Whether this step is mandatory
        depends_on: List of workflow names this depends on
        parallel_group: Group number for parallel execution (None = sequential)

    Example:
        ```python
        step = WorkflowStep(
            workflow_name="create-prd",
            phase="planning",
            required=True,
            depends_on=[],
            parallel_group=None
        )
        ```
    """

    workflow_name: str
    phase: str
    required: bool = True
    depends_on: List[str] = field(default_factory=list)
    parallel_group: Optional[int] = None


@dataclass
class WorkflowSequence:
    """Ordered sequence of workflows to execute.

    Methodologies build workflow sequences based on complexity assessment.
    Sequences define the order and dependencies of workflows.

    Attributes:
        workflows: List of workflow steps in execution order
        total_phases: Number of distinct phases
        estimated_duration: Expected time to complete
        can_parallelize: Whether workflows can run in parallel
        metadata: Methodology-specific additional data

    Example:
        ```python
        sequence = WorkflowSequence(
            workflows=[
                WorkflowStep("create-prd", "planning"),
                WorkflowStep("create-stories", "planning"),
                WorkflowStep("implement-stories", "implementation")
            ],
            total_phases=2,
            can_parallelize=False,
            metadata={"methodology": "bmad"}
        )
        ```
    """

    workflows: List[WorkflowStep] = field(default_factory=list)
    total_phases: int = 0
    estimated_duration: Optional[timedelta] = None
    can_parallelize: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of configuration validation.

    Methodologies validate their configuration settings and return
    structured validation results.

    Attributes:
        valid: Whether configuration is valid
        errors: List of error messages (prevent execution)
        warnings: List of warning messages (can continue)

    Example:
        ```python
        result = ValidationResult(
            valid=False,
            errors=["Invalid scale_level: 5. Must be 0-4."],
            warnings=["Unknown project_type: custom"]
        )

        if not result.valid:
            for error in result.errors:
                print(f"ERROR: {error}")
        ```
    """

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
