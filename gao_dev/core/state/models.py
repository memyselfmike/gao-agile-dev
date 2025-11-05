"""Data models for state tracking.

Provides typed dataclass models for all state entities:
- Story: Individual work items with status, owner, points
- Epic: Collections of stories with progress tracking
- Sprint: Time-boxed iterations with velocity metrics
- WorkflowExecution: Audit trail of workflow runs
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Story:
    """Story data model.

    Represents an individual work item with status tracking, ownership,
    and sprint assignment.

    Attributes:
        id: Database primary key
        epic: Epic number this story belongs to
        story_num: Story number within the epic
        title: Story title/name
        status: Current status (pending, in_progress, done, blocked, cancelled)
        owner: Assigned owner/agent
        points: Story points estimate
        priority: Priority level (P0-P3)
        sprint: Sprint number assignment (optional)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int
    epic: int
    story_num: int
    title: str
    status: str
    owner: Optional[str] = None
    points: int = 0
    priority: str = "P1"
    sprint: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""

    @property
    def full_id(self) -> str:
        """Return full story ID (e.g., '12.3').

        Returns:
            Full story identifier in format 'epic.story'
        """
        return f"{self.epic}.{self.story_num}"


@dataclass
class Epic:
    """Epic data model with computed progress.

    Represents a collection of related stories with automatic progress
    calculation and point tracking.

    Attributes:
        id: Database primary key
        epic_num: Epic number
        title: Epic title
        feature: Feature name this epic belongs to
        status: Epic status (planned, active, completed, cancelled)
        total_points: Total story points in epic
        completed_points: Completed story points
        progress: Completion percentage (computed)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int
    epic_num: int
    title: str
    feature: str
    status: str
    total_points: int = 0
    completed_points: int = 0
    progress: float = 0.0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        """Calculate progress percentage after initialization."""
        if self.total_points > 0:
            self.progress = (self.completed_points / self.total_points) * 100.0
        else:
            self.progress = 0.0


@dataclass
class Sprint:
    """Sprint data model.

    Represents a time-boxed iteration with velocity tracking.

    Attributes:
        id: Database primary key
        sprint_num: Sprint number
        name: Sprint name
        start_date: Sprint start date (ISO format)
        end_date: Sprint end date (ISO format)
        status: Sprint status (planned, active, completed, cancelled)
        created_at: Creation timestamp
    """

    id: int
    sprint_num: int
    name: str
    start_date: str
    end_date: str
    status: str
    created_at: str = ""


@dataclass
class WorkflowExecution:
    """Workflow execution record.

    Tracks execution history of workflows for audit and debugging.

    Attributes:
        id: Database primary key
        workflow_id: Unique workflow execution identifier
        epic: Epic number (if applicable)
        story_num: Story number (if applicable)
        workflow_name: Name of executed workflow
        status: Execution status (started, running, completed, failed, cancelled)
        started_at: Start timestamp
        completed_at: Completion timestamp (optional)
        result: Execution result/output (optional)
    """

    id: int
    workflow_id: str
    epic: int
    story_num: int
    workflow_name: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    result: Optional[str] = None
