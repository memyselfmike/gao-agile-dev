"""
Workflow domain models and value objects.

This module contains value objects and models for workflows.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum


@dataclass(frozen=True)
class WorkflowIdentifier:
    """
    Immutable identifier for a workflow.

    Workflows are identified by name, phase, and optionally version.

    Attributes:
        name: Workflow name (e.g., "create-story", "prd")
        phase: BMAD phase (0-4) or -1 for phase-independent
        version: Optional version string

    Example:
        ```python
        workflow_id = WorkflowIdentifier("create-story", phase=4)
        print(workflow_id.to_string())  # "create-story (phase 4)"

        # Create from string
        workflow_id = WorkflowIdentifier.from_string("prd")
        ```
    """

    name: str
    phase: int = -1  # -1 means phase-independent
    version: Optional[str] = None

    def __post_init__(self):
        """Validate workflow identifier."""
        if not self.name:
            raise ValueError("Workflow name cannot be empty")
        if self.phase < -1 or self.phase > 4:
            raise ValueError(f"Phase must be -1 to 4, got {self.phase}")

    def to_string(self) -> str:
        """
        Convert to string format.

        Returns:
            str: Workflow identifier as "name (phase X)" or just "name"
        """
        if self.phase >= 0:
            base = f"{self.name} (phase {self.phase})"
        else:
            base = self.name

        if self.version:
            return f"{base} v{self.version}"
        return base

    def to_path(self) -> Path:
        """
        Convert to file system path.

        Returns:
            Path: Path like "workflows/{phase}-{name}" or "workflows/{name}"
        """
        if self.phase >= 0:
            return Path("workflows") / f"{self.phase}-{self.name}"
        return Path("workflows") / self.name

    @classmethod
    def from_string(cls, s: str) -> 'WorkflowIdentifier':
        """
        Parse from string format.

        Args:
            s: String like "create-story" or "prd (phase 2)"

        Returns:
            WorkflowIdentifier instance
        """
        # Simple case: just name
        if "(" not in s:
            return cls(name=s.strip())

        # With phase: "name (phase X)"
        parts = s.split("(")
        name = parts[0].strip()

        phase = -1
        if "phase" in parts[1]:
            phase_str = parts[1].split("phase")[1].strip().rstrip(")")
            phase = int(phase_str)

        return cls(name=name, phase=phase)

    def __str__(self) -> str:
        """String representation."""
        return self.to_string()

    def __repr__(self) -> str:
        """Developer representation."""
        return f"WorkflowIdentifier('{self.name}', phase={self.phase})"


@dataclass(frozen=True)
class ComplexityLevel:
    """
    Project complexity level value object.

    Represents assessed complexity with level, description, and estimates.
    Methodology-agnostic (not tied to BMAD scale levels).

    Attributes:
        level: Complexity level (0-4, higher is more complex)
        description: Human-readable description
        estimated_stories_min: Minimum estimated stories
        estimated_stories_max: Maximum estimated stories
        estimated_epics: Estimated number of epics

    Example:
        ```python
        # Create complexity level
        complexity = ComplexityLevel(
            level=3,
            description="Large project",
            estimated_stories_min=12,
            estimated_stories_max=40,
            estimated_epics=3
        )

        # Factory methods
        complexity = ComplexityLevel.from_scale_level(3)
        complexity = ComplexityLevel.from_story_count(25)
        ```
    """

    level: int
    description: str
    estimated_stories_min: int
    estimated_stories_max: int
    estimated_epics: int = 1

    def __post_init__(self):
        """Validate complexity level."""
        if self.level < 0 or self.level > 4:
            raise ValueError(f"Level must be 0-4, got {self.level}")
        if self.estimated_stories_min < 1:
            raise ValueError(f"Min stories must be >= 1, got {self.estimated_stories_min}")
        if self.estimated_stories_max < self.estimated_stories_min:
            raise ValueError(
                f"Max stories ({self.estimated_stories_max}) must be >= "
                f"min stories ({self.estimated_stories_min})"
            )

    @classmethod
    def from_scale_level(cls, scale_level: int) -> 'ComplexityLevel':
        """
        Create from BMAD scale level.

        Args:
            scale_level: BMAD scale level (0-4)

        Returns:
            ComplexityLevel instance
        """
        # BMAD scale mapping
        scale_mapping = {
            0: (0, "Atomic change", 1, 1, 1),
            1: (1, "Simple feature", 1, 3, 1),
            2: (2, "Feature set", 4, 11, 1),
            3: (3, "Large project", 12, 40, 3),
            4: (4, "Massive undertaking", 41, 100, 5),
        }

        if scale_level not in scale_mapping:
            raise ValueError(f"Invalid scale level: {scale_level}")

        level, desc, min_stories, max_stories, epics = scale_mapping[scale_level]
        return cls(
            level=level,
            description=desc,
            estimated_stories_min=min_stories,
            estimated_stories_max=max_stories,
            estimated_epics=epics,
        )

    @classmethod
    def from_story_count(cls, story_count: int) -> 'ComplexityLevel':
        """
        Create from estimated story count.

        Args:
            story_count: Estimated number of stories

        Returns:
            ComplexityLevel instance
        """
        if story_count == 1:
            return cls.from_scale_level(0)
        elif story_count <= 3:
            return cls.from_scale_level(1)
        elif story_count <= 11:
            return cls.from_scale_level(2)
        elif story_count <= 40:
            return cls.from_scale_level(3)
        else:
            return cls.from_scale_level(4)

    def __lt__(self, other: 'ComplexityLevel') -> bool:
        """Less than comparison by level."""
        return self.level < other.level

    def __le__(self, other: 'ComplexityLevel') -> bool:
        """Less than or equal comparison by level."""
        return self.level <= other.level

    def __gt__(self, other: 'ComplexityLevel') -> bool:
        """Greater than comparison by level."""
        return self.level > other.level

    def __ge__(self, other: 'ComplexityLevel') -> bool:
        """Greater than or equal comparison by level."""
        return self.level >= other.level

    def __str__(self) -> str:
        """String representation."""
        return f"Level {self.level}: {self.description}"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"ComplexityLevel(level={self.level}, description='{self.description}')"


@dataclass
class WorkflowContext:
    """
    Context for workflow execution.

    Contains all information needed for a workflow to execute:
    project paths, parameters, previous workflow results, etc.

    Attributes:
        project_root: Root path of the project
        parameters: Workflow-specific parameters
        artifacts: Artifacts from previous workflows
        metadata: Additional metadata
    """

    project_root: Path
    parameters: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value."""
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any) -> None:
        """Set a parameter value."""
        self.parameters[key] = value

    def get_artifact(self, key: str) -> Optional[Any]:
        """Get an artifact from previous workflows."""
        return self.artifacts.get(key)

    def add_artifact(self, key: str, value: Any) -> None:
        """Add an artifact for subsequent workflows."""
        self.artifacts[key] = value


@dataclass
class WorkflowResult:
    """
    Result of workflow execution.

    Attributes:
        success: Whether workflow completed successfully
        workflow_name: Name of the workflow
        artifacts: Created artifacts (file paths, data, etc.)
        errors: List of errors if any
        metadata: Additional result metadata
    """

    success: bool
    workflow_name: str
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "workflow_name": self.workflow_name,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowSequence:
    """
    Sequence of workflows to execute.

    Represents an ordered list of workflows with dependencies.

    Attributes:
        workflows: List of workflow identifiers in execution order
        description: Optional description of the sequence
    """

    workflows: List[WorkflowIdentifier]
    description: Optional[str] = None

    def __len__(self) -> int:
        """Number of workflows in sequence."""
        return len(self.workflows)

    def __iter__(self):
        """Iterate over workflows."""
        return iter(self.workflows)

    def __getitem__(self, index: int) -> WorkflowIdentifier:
        """Get workflow by index."""
        return self.workflows[index]


@dataclass
class WorkflowInfo:
    """Workflow metadata and configuration.

    This is the primary model for workflow information used throughout GAO-Dev.
    It contains all metadata needed to discover, load, and execute workflows.

    Attributes:
        name: Workflow name (e.g., "create-story", "prd")
        description: Human-readable description
        phase: BMAD phase (0-4) when applicable
        installed_path: Path where workflow is installed
        author: Optional author name
        tags: List of classification tags
        variables: Dictionary of workflow variables
        required_tools: Tools required for execution
        interactive: Whether workflow is interactive
        autonomous: Whether workflow can run autonomously
        iterative: Whether workflow is iterative
        web_bundle: Whether workflow has web components
        output_file: Optional output file path template
        templates: Dictionary of template mappings
    """

    name: str
    description: str
    phase: int
    installed_path: Path
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    required_tools: List[str] = field(default_factory=list)
    interactive: bool = True
    autonomous: bool = True
    iterative: bool = False
    web_bundle: bool = False
    output_file: Optional[str] = None
    templates: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "phase": self.phase,
            "installed_path": str(self.installed_path),  # Convert Path to string
            "author": self.author,
            "tags": self.tags,
            "variables": self.variables,
            "required_tools": self.required_tools,
            "interactive": self.interactive,
            "autonomous": self.autonomous,
            "iterative": self.iterative,
            "web_bundle": self.web_bundle,
            "output_file": self.output_file,
            "templates": self.templates,
        }
