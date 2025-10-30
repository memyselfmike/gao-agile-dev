"""
Workflow context models.

This module defines context models for workflow execution and strategy selection.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import enums from brian_orchestrator (will move to models later)
from ...orchestrator.brian_orchestrator import ScaleLevel, ProjectType, PromptAnalysis


@dataclass
class WorkflowContext:
    """
    Context for workflow execution and strategy selection.

    Contains all information needed to select and execute appropriate workflows,
    including scale level, project type, analysis results, and custom parameters.

    Attributes:
        initial_prompt: User's initial request/prompt
        project_root: Root directory of the project
        scale_level: Project scale level (0-4)
        project_type: Type of project
        analysis: Full prompt analysis results
        custom_workflows: Optional explicit workflow sequence
        metadata: Additional context metadata
    """

    initial_prompt: str
    project_root: Optional[Path] = None
    scale_level: Optional[ScaleLevel] = None
    project_type: Optional[ProjectType] = None
    analysis: Optional[PromptAnalysis] = None
    custom_workflows: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_greenfield(self) -> bool:
        """Check if this is a greenfield project."""
        if self.analysis:
            return self.analysis.is_greenfield
        return self.project_type == ProjectType.GREENFIELD if self.project_type else False

    @property
    def is_brownfield(self) -> bool:
        """Check if this is a brownfield project."""
        if self.analysis:
            return self.analysis.is_brownfield
        return self.project_type == ProjectType.BROWNFIELD if self.project_type else False

    @property
    def is_game_project(self) -> bool:
        """Check if this is a game project."""
        if self.analysis:
            return self.analysis.is_game_project
        return self.project_type == ProjectType.GAME if self.project_type else False

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value
