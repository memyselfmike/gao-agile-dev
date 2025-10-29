"""
Agent domain models and value objects.

This module contains value objects and models for agents.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path


class AgentCapabilityType(Enum):
    """
    Agent capability types enumeration.

    Defines standard capability categories for agents.
    """

    # Planning capabilities
    ANALYSIS = "analysis"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    UX_DESIGN = "ux-design"

    # Implementation capabilities
    IMPLEMENTATION = "implementation"
    CODE_REVIEW = "code-review"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"

    # Testing capabilities
    TESTING = "testing"
    QA = "qa"
    PERFORMANCE_TESTING = "performance-testing"

    # Management capabilities
    PROJECT_MANAGEMENT = "project-management"
    SCRUM_MASTER = "scrum-master"
    COORDINATION = "coordination"

    # Documentation capabilities
    DOCUMENTATION = "documentation"
    TECHNICAL_WRITING = "technical-writing"

    # DevOps capabilities
    CI_CD = "ci-cd"
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE = "infrastructure"


@dataclass(frozen=True)
class AgentCapability:
    """
    Immutable value object representing an agent capability.

    Capabilities define what kinds of tasks an agent can handle.
    Each capability has a type, description, and required tools.

    Attributes:
        capability_type: Type of capability
        description: Human-readable description
        required_tools: Tools required for this capability
        confidence_level: Optional confidence level (0.0-1.0)

    Example:
        ```python
        capability = AgentCapability(
            capability_type=AgentCapabilityType.IMPLEMENTATION,
            description="Implement user stories with tests",
            required_tools=["Read", "Write", "Edit", "Bash"],
            confidence_level=0.9
        )
        ```
    """

    capability_type: AgentCapabilityType
    description: str
    required_tools: tuple  # Immutable tuple instead of list
    confidence_level: float = 1.0

    def __post_init__(self):
        """Validate capability."""
        if not self.description:
            raise ValueError("Description cannot be empty")
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueError(f"Confidence level must be 0.0-1.0, got {self.confidence_level}")

    @classmethod
    def create(
        cls,
        capability_type: AgentCapabilityType,
        description: str,
        required_tools: List[str],
        confidence_level: float = 1.0
    ) -> 'AgentCapability':
        """
        Create capability with tools list (converts to tuple).

        Args:
            capability_type: Capability type
            description: Description
            required_tools: List of required tools
            confidence_level: Confidence level (0.0-1.0)

        Returns:
            AgentCapability instance
        """
        return cls(
            capability_type=capability_type,
            description=description,
            required_tools=tuple(required_tools),
            confidence_level=confidence_level
        )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.capability_type.value}: {self.description}"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"AgentCapability("
            f"type={self.capability_type.value}, "
            f"confidence={self.confidence_level})"
        )


# Predefined common capabilities
class CommonCapabilities:
    """Common predefined capabilities for quick use."""

    ANALYSIS = AgentCapability.create(
        AgentCapabilityType.ANALYSIS,
        "Business analysis and requirements gathering",
        ["Read", "Write", "WebFetch", "WebSearch"]
    )

    PLANNING = AgentCapability.create(
        AgentCapabilityType.PLANNING,
        "Product planning and feature definition",
        ["Read", "Write", "Grep", "Glob"]
    )

    ARCHITECTURE = AgentCapability.create(
        AgentCapabilityType.ARCHITECTURE,
        "System architecture and technical design",
        ["Read", "Write", "Grep", "Glob"]
    )

    UX_DESIGN = AgentCapability.create(
        AgentCapabilityType.UX_DESIGN,
        "User experience and interface design",
        ["Read", "Write"]
    )

    IMPLEMENTATION = AgentCapability.create(
        AgentCapabilityType.IMPLEMENTATION,
        "Code implementation and development",
        ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    )

    CODE_REVIEW = AgentCapability.create(
        AgentCapabilityType.CODE_REVIEW,
        "Code review and quality assessment",
        ["Read", "Grep", "Glob"]
    )

    TESTING = AgentCapability.create(
        AgentCapabilityType.TESTING,
        "Test creation and quality assurance",
        ["Read", "Write", "Edit", "Bash", "Grep"]
    )

    PROJECT_MANAGEMENT = AgentCapability.create(
        AgentCapabilityType.PROJECT_MANAGEMENT,
        "Project management and coordination",
        ["Read", "Write", "Grep", "Glob"]
    )

    SCRUM_MASTER = AgentCapability.create(
        AgentCapabilityType.SCRUM_MASTER,
        "Scrum facilitation and story management",
        ["Read", "Write", "Grep", "Glob"]
    )

    DOCUMENTATION = AgentCapability.create(
        AgentCapabilityType.DOCUMENTATION,
        "Documentation creation and maintenance",
        ["Read", "Write", "Edit"]
    )


@dataclass
class AgentContext:
    """
    Context for agent task execution.

    Contains all information an agent needs to execute a task:
    project paths, available tools, configuration, etc.

    Attributes:
        project_root: Root path of the project
        available_tools: Tools available to the agent
        agent_config: Agent-specific configuration
        workflow_context: Optional workflow context if part of workflow
        metadata: Additional metadata
    """

    project_root: Path
    available_tools: List[str] = field(default_factory=list)
    agent_config: Dict[str, Any] = field(default_factory=dict)
    workflow_context: Optional[Any] = None  # WorkflowContext
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_tool(self, tool: str) -> bool:
        """Check if a tool is available."""
        return tool in self.available_tools

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.agent_config.get(key, default)


@dataclass
class AgentConfig:
    """
    Configuration for an agent.

    Attributes:
        name: Agent name
        role: Agent role
        persona_file: Path to persona markdown file
        tools: List of allowed tools
        max_iterations: Maximum task iterations
        timeout: Task timeout in seconds
        custom_config: Additional custom configuration
    """

    name: str
    role: str
    persona_file: Optional[Path] = None
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 10
    timeout: int = 3600  # 1 hour
    custom_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "persona_file": str(self.persona_file) if self.persona_file else None,
            "tools": self.tools,
            "max_iterations": self.max_iterations,
            "timeout": self.timeout,
            "custom_config": self.custom_config,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentConfig':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            role=data["role"],
            persona_file=Path(data["persona_file"]) if data.get("persona_file") else None,
            tools=data.get("tools", []),
            max_iterations=data.get("max_iterations", 10),
            timeout=data.get("timeout", 3600),
            custom_config=data.get("custom_config", {}),
        )
