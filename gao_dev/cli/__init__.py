"""CLI interface for GAO-Dev."""

from .commands import cli
from .sandbox_commands import sandbox
from .project_detection import (
    detect_project_root,
    is_project_root,
    find_all_projects,
    get_project_name,
)

__all__ = [
    "cli",
    "sandbox",
    "detect_project_root",
    "is_project_root",
    "find_all_projects",
    "get_project_name",
]
