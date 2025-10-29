"""Core data models for GAO-Dev."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


@dataclass
class WorkflowInfo:
    """Workflow metadata and configuration."""

    name: str
    description: str
    phase: int
    installed_path: Path
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    required_tools: List[str] = field(default_factory=list)
    interactive: bool = True
    autonomous: bool = True
    iterative: bool = False
    web_bundle: bool = False
    output_file: Optional[str] = None
    templates: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "phase": self.phase,
            "author": self.author,
            "tags": self.tags,
            "variables": self.variables,
            "required_tools": self.required_tools,
            "interactive": self.interactive,
            "autonomous": self.autonomous,
            "iterative": self.iterative,
            "web_bundle": self.web_bundle,
            "output_file": self.output_file,
            "templates": self.templates,
        }


class StoryStatus(Enum):
    """Story status enumeration."""

    DRAFT = "draft"
    READY = "ready"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    DONE = "done"


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """Individual health check result."""

    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details or {},
            "remediation": self.remediation,
        }


@dataclass
class HealthCheckResult:
    """Overall health check result."""

    status: HealthStatus
    checks: List[CheckResult]
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
            "summary": self.summary,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentInfo:
    """Agent persona information."""

    name: str
    role: str
    file_path: Path
    workflows: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "workflows": self.workflows,
            "responsibilities": self.responsibilities,
        }
