"""
Project domain models and value objects.

This module contains value objects and models for projects.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from enum import Enum


class ProjectStatus(Enum):
    """Project status enumeration."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass(frozen=True)
class ProjectPath:
    """
    Immutable value object encapsulating all paths for a GAO-Dev project.

    This value object provides type-safe access to all standard paths
    in a GAO-Dev project structure, with validation that the root exists.

    Attributes:
        root: Absolute path to project root directory

    Example:
        ```python
        project = ProjectPath(Path("D:/My Projects/todo-app").absolute())

        # Access standard paths
        docs_dir = project.docs
        prd_file = project.prd
        stories_dir = project.stories
        story_file = project.story_path(1, 1)
        ```
    """

    root: Path

    def __post_init__(self):
        """Validate root path."""
        # Use object.__setattr__ for frozen dataclass
        if not self.root.is_absolute():
            raise ValueError(f"Project root must be absolute path, got: {self.root}")
        if not self.root.exists():
            raise ValueError(f"Project root does not exist: {self.root}")

    # Documentation paths
    @property
    def docs(self) -> Path:
        """Documentation directory (docs/)."""
        return self.root / "docs"

    @property
    def features(self) -> Path:
        """Features directory (docs/features/)."""
        return self.docs / "features"

    @property
    def stories(self) -> Path:
        """Stories directory (docs/stories/)."""
        return self.docs / "stories"

    @property
    def prd(self) -> Path:
        """PRD file path (docs/PRD.md)."""
        return self.docs / "PRD.md"

    @property
    def architecture(self) -> Path:
        """Architecture file path (docs/ARCHITECTURE.md)."""
        return self.docs / "ARCHITECTURE.md"

    @property
    def epics(self) -> Path:
        """Epics file path (docs/epics.md)."""
        return self.docs / "epics.md"

    @property
    def tech_stack(self) -> Path:
        """Tech stack file path (docs/tech-stack.md)."""
        return self.docs / "tech-stack.md"

    # Source code paths
    @property
    def src(self) -> Path:
        """Source code directory (src/)."""
        return self.root / "src"

    @property
    def tests(self) -> Path:
        """Tests directory (tests/)."""
        return self.root / "tests"

    # Configuration paths
    @property
    def config(self) -> Path:
        """Configuration directory (.gao/ or config/)."""
        gao_config = self.root / ".gao"
        if gao_config.exists():
            return gao_config
        return self.root / "config"

    @property
    def workflows_dir(self) -> Path:
        """Workflows directory (.gao/workflows/ or workflows/)."""
        return self.config / "workflows"

    # Build/output paths
    @property
    def build(self) -> Path:
        """Build output directory (build/ or dist/)."""
        build_dir = self.root / "build"
        if build_dir.exists():
            return build_dir
        return self.root / "dist"

    # Helper methods
    def story_path(self, epic: int, story: int) -> Path:
        """
        Get path to a specific story file.

        Args:
            epic: Epic number
            story: Story number

        Returns:
            Path: Absolute path to story file

        Example:
            ```python
            path = project.story_path(1, 1)
            # D:/My Projects/todo-app/docs/stories/epic-1/story-1.1.md
            ```
        """
        return self.stories / f"epic-{epic}" / f"story-{epic}.{story}.md"

    def epic_dir(self, epic: int) -> Path:
        """
        Get path to epic directory.

        Args:
            epic: Epic number

        Returns:
            Path: Absolute path to epic directory
        """
        return self.stories / f"epic-{epic}"

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            dict: Dictionary with root path
        """
        return {"root": str(self.root)}

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectPath':
        """
        Create from dictionary.

        Args:
            data: Dictionary with 'root' key

        Returns:
            ProjectPath instance
        """
        return cls(root=Path(data["root"]))

    def __str__(self) -> str:
        """String representation."""
        return str(self.root)

    def __repr__(self) -> str:
        """Developer representation."""
        return f"ProjectPath('{self.root}')"


@dataclass
class Project:
    """
    Project model.

    Represents a GAO-Dev project with metadata and configuration.

    Attributes:
        id: Unique project identifier
        name: Project name
        path: Project path value object
        status: Current project status
        description: Optional project description
        methodology: Methodology name (e.g., "BMAD", "Scrum")
        tags: Optional list of tags
    """

    id: str
    name: str
    path: ProjectPath
    status: ProjectStatus
    description: Optional[str] = None
    methodology: str = "BMAD"
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path.root),
            "status": self.status.value,
            "description": self.description,
            "methodology": self.methodology,
            "tags": self.tags or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=ProjectPath(Path(data["path"])),
            status=ProjectStatus(data["status"]),
            description=data.get("description"),
            methodology=data.get("methodology", "BMAD"),
            tags=data.get("tags"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
