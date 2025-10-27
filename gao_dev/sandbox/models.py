"""Data models for sandbox management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class ProjectStatus(Enum):
    """Status of a sandbox project."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class BenchmarkRun:
    """Represents a single benchmark run within a project."""

    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    config_file: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "config_file": self.config_file,
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkRun":
        """Load from dictionary."""
        return cls(
            run_id=data["run_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            status=ProjectStatus(data["status"]),
            config_file=data.get("config_file", ""),
            metrics=data.get("metrics", {}),
        )


@dataclass
class ProjectMetadata:
    """Metadata for a sandbox project."""

    name: str
    created_at: datetime
    status: ProjectStatus = ProjectStatus.ACTIVE
    boilerplate_url: Optional[str] = None
    last_modified: datetime = field(default_factory=datetime.now)
    runs: List[BenchmarkRun] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    benchmark_info: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "boilerplate_url": self.boilerplate_url,
            "last_modified": self.last_modified.isoformat(),
            "runs": [run.to_dict() for run in self.runs],
            "tags": self.tags,
            "description": self.description,
        }

        if self.benchmark_info:
            result["benchmark_info"] = self.benchmark_info

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectMetadata":
        """Load from dictionary."""
        return cls(
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            status=ProjectStatus(data["status"]),
            boilerplate_url=data.get("boilerplate_url"),
            last_modified=datetime.fromisoformat(data.get("last_modified", data["created_at"])),
            runs=[BenchmarkRun.from_dict(run) for run in data.get("runs", [])],
            tags=data.get("tags", []),
            description=data.get("description", ""),
            benchmark_info=data.get("benchmark_info"),
        )

    def add_run(self, run: BenchmarkRun) -> None:
        """Add a benchmark run to this project."""
        self.runs.append(run)
        self.last_modified = datetime.now()

    def get_run_count(self) -> int:
        """Get total number of runs."""
        return len(self.runs)

    def get_latest_run(self) -> Optional[BenchmarkRun]:
        """Get the most recent benchmark run."""
        if not self.runs:
            return None
        return max(self.runs, key=lambda r: r.started_at)
