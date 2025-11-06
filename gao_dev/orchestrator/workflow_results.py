"""Data classes for workflow results."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class StoryStatus(Enum):
    """Status of a story execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    QA_VALIDATION = "qa_validation"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStepResult:
    """Result of executing a single workflow step."""
    step_name: str
    agent: str
    status: str  # success, failed, skipped
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    artifacts_created: List[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None
    output: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_name": self.step_name,
            "agent": self.agent,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "artifacts_created": self.artifacts_created,
            "commit_hash": self.commit_hash,
            "error_message": self.error_message,
            "output": self.output[:500] if self.output else "",  # Truncate for serialization
            "metrics": self.metrics,
        }


@dataclass
class WorkflowResult:
    """Result of executing complete workflow."""
    workflow_name: str
    initial_prompt: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    step_results: List[WorkflowStepResult] = field(default_factory=list)
    total_artifacts: int = 0
    project_path: Optional[str] = None
    error_message: Optional[str] = None
    context_id: Optional[str] = None  # Link to WorkflowContext for traceability

    @property
    def success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == WorkflowStatus.COMPLETED

    @property
    def duration_seconds(self) -> float:
        """Total workflow duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def total_steps(self) -> int:
        """Total number of steps."""
        return len(self.step_results)

    @property
    def successful_steps(self) -> int:
        """Number of successful steps."""
        return sum(1 for step in self.step_results if step.status == "success")

    @property
    def failed_steps(self) -> int:
        """Number of failed steps."""
        return sum(1 for step in self.step_results if step.status == "failed")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_name": self.workflow_name,
            "initial_prompt": self.initial_prompt,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "total_artifacts": self.total_artifacts,
            "project_path": self.project_path,
            "error_message": self.error_message,
            "context_id": self.context_id,
            "step_results": [step.to_dict() for step in self.step_results],
        }


@dataclass
class StoryResult:
    """Result of executing a single story."""

    story_name: str
    epic_name: str
    agent: str
    status: StoryStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    artifacts_created: List[str] = field(default_factory=list)
    commit_hash: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "story_name": self.story_name,
            "epic_name": self.epic_name,
            "agent": self.agent,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "artifacts_created": self.artifacts_created,
            "commit_hash": self.commit_hash,
            "metrics": self.metrics,
        }


@dataclass
class EpicResult:
    """Result of executing an entire epic."""

    epic_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    story_results: List[StoryResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if all stories completed successfully."""
        return all(
            story.status == StoryStatus.COMPLETED
            for story in self.story_results
        )

    @property
    def total_stories(self) -> int:
        """Total number of stories."""
        return len(self.story_results)

    @property
    def completed_stories(self) -> int:
        """Number of completed stories."""
        return sum(
            1 for story in self.story_results
            if story.status == StoryStatus.COMPLETED
        )

    @property
    def failed_stories(self) -> int:
        """Number of failed stories."""
        return sum(
            1 for story in self.story_results
            if story.status == StoryStatus.FAILED
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "epic_name": self.epic_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_stories": self.total_stories,
            "completed_stories": self.completed_stories,
            "failed_stories": self.failed_stories,
            "success": self.success,
            "story_results": [story.to_dict() for story in self.story_results],
        }
