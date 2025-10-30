"""Orchestrator-specific models.

Story 5.4: Models extracted from brian_orchestrator.py for orchestrator use.
These are kept separate from core methodology models as they're specific to
the orchestrator's implementation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

from ..core.legacy_models import WorkflowInfo


class ScaleLevel(Enum):
    """Scale levels for project complexity (scale-adaptive approach).

    Story 5.4: Moved from brian_orchestrator.py. This is orchestrator-specific
    and maps to ComplexityLevel for methodology operations.
    """

    LEVEL_0 = 0  # Single atomic change (1 story)
    LEVEL_1 = 1  # Small feature (2-10 stories, 1 epic)
    LEVEL_2 = 2  # Medium project (5-15 stories, 1-2 epics)
    LEVEL_3 = 3  # Large project (12-40 stories, 2-5 epics)
    LEVEL_4 = 4  # Enterprise system (40+ stories, 5+ epics)


class ProjectType(Enum):
    """Project type classification for orchestrator.

    Story 5.4: Moved from brian_orchestrator.py. This represents project
    approach (greenfield vs brownfield) rather than technical type.
    """

    GREENFIELD = "greenfield"  # New project from scratch
    BROWNFIELD = "brownfield"  # Enhancing existing codebase
    GAME = "game"  # Game development project
    SOFTWARE = "software"  # Standard software project
    BUG_FIX = "bug_fix"  # Bug fix only
    ENHANCEMENT = "enhancement"  # Feature enhancement


@dataclass
class PromptAnalysis:
    """Analysis results from initial prompt assessment.

    Story 5.4: Moved from brian_orchestrator.py for orchestrator use.
    """

    scale_level: ScaleLevel
    project_type: ProjectType
    is_greenfield: bool
    is_brownfield: bool
    is_game_project: bool
    estimated_stories: int
    estimated_epics: int
    technical_complexity: str  # low, medium, high
    domain_complexity: str  # low, medium, high
    timeline_hint: Optional[str]  # hours, days, weeks, months
    confidence: float  # 0.0-1.0
    reasoning: str
    needs_clarification: bool = False
    clarifying_questions: List[str] = field(default_factory=list)


@dataclass
class WorkflowSequence:
    """Sequence of workflows to execute for a project.

    Story 5.4: Moved from brian_orchestrator.py for orchestrator use.
    """

    scale_level: ScaleLevel
    workflows: List[WorkflowInfo]
    project_type: ProjectType
    routing_rationale: str
    phase_breakdown: Dict[str, List[str]]  # Phase name -> workflow names
    jit_tech_specs: bool = False  # Just-in-time tech specs (Level 3-4)
