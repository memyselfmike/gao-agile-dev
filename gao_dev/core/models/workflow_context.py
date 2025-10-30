"""
Workflow context models.

This module defines context models for workflow execution and strategy selection.

Story 5.4: Refactored to use generic methodology models instead of BMAD-specific types.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..models.methodology import (
    ComplexityLevel,
    ComplexityAssessment,
    ProjectType,
)


@dataclass
class WorkflowContext:
    """
    Context for workflow execution and strategy selection.

    Contains all information needed to select and execute appropriate workflows,
    including complexity level, project type, assessment results, and custom parameters.

    Story 5.4: Updated to use generic methodology models (ComplexityLevel instead of ScaleLevel).

    Attributes:
        initial_prompt: User's initial request/prompt
        project_root: Root directory of the project
        complexity_level: Project complexity level (TRIVIAL, SMALL, MEDIUM, LARGE, XLARGE)
        project_type: Type of project (WEB_APP, API, CLI, etc.)
        assessment: Full complexity assessment results
        custom_workflows: Optional explicit workflow sequence
        metadata: Additional context metadata (can include scale_level, is_greenfield, etc.)
    """

    initial_prompt: str
    project_root: Optional[Path] = None
    complexity_level: Optional[ComplexityLevel] = None
    project_type: Optional[ProjectType] = None
    assessment: Optional[ComplexityAssessment] = None
    custom_workflows: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Backward compatibility: map old scale_level to complexity_level
    @property
    def scale_level(self) -> Optional[int]:
        """Backward compatibility: Get scale level from metadata.

        Returns:
            Scale level (0-4) if present in metadata, None otherwise
        """
        return self.metadata.get("scale_level")

    @property
    def is_greenfield(self) -> bool:
        """Check if this is a greenfield project.

        Returns:
            True if metadata indicates greenfield project
        """
        return self.metadata.get("is_greenfield", False)

    @property
    def is_brownfield(self) -> bool:
        """Check if this is a brownfield project.

        Returns:
            True if metadata indicates brownfield project
        """
        return self.metadata.get("is_brownfield", False)

    @property
    def is_game_project(self) -> bool:
        """Check if this is a game project.

        Returns:
            True if metadata indicates game project
        """
        return self.metadata.get("is_game_project", False)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value
