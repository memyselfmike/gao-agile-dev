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
