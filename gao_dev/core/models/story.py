"""
Story domain models and value objects.

This module contains value objects and models for user stories.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from enum import Enum


class StoryStatus(Enum):
    """
    Story status enumeration.

    Represents the current state of a user story in its lifecycle.
    """

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DONE = "done"


@dataclass(frozen=True)
class StoryIdentifier:
    """
    Immutable identifier for a user story.

    Stories are identified by their epic and story numbers.
    Example: Epic 1, Story 3 → StoryIdentifier(1, 3)

    Attributes:
        epic: Epic number (>= 1)
        story: Story number within epic (>= 1)

    Example:
        ```python
        story_id = StoryIdentifier(1, 1)
        print(story_id.to_string())  # "1.1"
        print(story_id.to_path())    # Path("epic-1/story-1.1.md")

        # Parse from string
        story_id = StoryIdentifier.from_string("2.3")
        ```
    """

    epic: int
    story: int

    def __post_init__(self):
        """Validate story identifier."""
        if self.epic < 1:
            raise ValueError(f"Epic must be >= 1, got {self.epic}")
        if self.story < 1:
            raise ValueError(f"Story must be >= 1, got {self.story}")

    def to_string(self) -> str:
        """
        Convert to string format "E.S".

        Returns:
            str: Story identifier as "1.1", "2.3", etc.
        """
        return f"{self.epic}.{self.story}"

    def to_path(self, relative: bool = True) -> Path:
        """
        Convert to file path.

        Args:
            relative: If True, returns relative path (default)

        Returns:
            Path: Path like "epic-1/story-1.1.md"
        """
        return Path(f"epic-{self.epic}") / f"story-{self.epic}.{self.story}.md"

    def to_key(self) -> str:
        """
        Convert to key format for sprint-status.yaml.

        Returns:
            str: Key like "1-1" for epic 1, story 1
        """
        return f"{self.epic}-{self.story}"

    @classmethod
    def from_string(cls, s: str) -> 'StoryIdentifier':
        """
        Parse from string format "E.S".

        Args:
            s: String like "1.1" or "2.3"

        Returns:
            StoryIdentifier instance

        Raises:
            ValueError: If string format invalid

        Example:
            ```python
            story_id = StoryIdentifier.from_string("1.1")
            ```
        """
        try:
            epic_str, story_str = s.split('.')
            return cls(epic=int(epic_str), story=int(story_str))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid story identifier: {s}") from e

    @classmethod
    def from_key(cls, key: str) -> 'StoryIdentifier':
        """
        Parse from key format "E-S".

        Args:
            key: Key like "1-1" or "2-3"

        Returns:
            StoryIdentifier instance

        Raises:
            ValueError: If key format invalid
        """
        try:
            epic_str, story_str = key.split('-', 1)
            return cls(epic=int(epic_str), story=int(story_str))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid story key: {key}") from e

    def __str__(self) -> str:
        """String representation."""
        return self.to_string()

    def __repr__(self) -> str:
        """Developer representation."""
        return f"StoryIdentifier({self.epic}, {self.story})"


@dataclass
class Story:
    """
    User story model.

    Represents a user story with its metadata and status.

    Attributes:
        id: Story identifier
        title: Story title
        status: Current story status
        file_path: Path to story file
        epic_title: Optional epic title
        story_points: Optional story points
        assigned_to: Optional assigned agent
    """

    id: StoryIdentifier
    title: str
    status: StoryStatus
    file_path: Path
    epic_title: Optional[str] = None
    story_points: Optional[int] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[list] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "epic": self.id.epic,
            "story": self.id.story,
            "title": self.title,
            "status": self.status.value,
            "file_path": str(self.file_path),
            "epic_title": self.epic_title,
            "story_points": self.story_points,
            "assigned_to": self.assigned_to,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Story':
        """Create from dictionary."""
        return cls(
            id=StoryIdentifier(data["epic"], data["story"]),
            title=data["title"],
            status=StoryStatus(data["status"]),
            file_path=Path(data["file_path"]),
            epic_title=data.get("epic_title"),
            story_points=data.get("story_points"),
            assigned_to=data.get("assigned_to"),
            description=data.get("description"),
            acceptance_criteria=data.get("acceptance_criteria"),
        )
