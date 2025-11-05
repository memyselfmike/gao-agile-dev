"""State tracking database module for GAO-Dev.

This module provides a comprehensive SQLite-based state tracking system for:
- Epics, stories, sprints, and workflow executions
- Complete audit trail of all state changes
- Performance-optimized queries (<50ms)
- Migration system with upgrade/downgrade support
- Schema validation and integrity checks
"""

from pathlib import Path

from .models import Story, Epic, Sprint, WorkflowExecution
from .exceptions import (
    StateTrackerError,
    RecordNotFoundError,
    ValidationError,
    DatabaseConnectionError,
    TransactionError,
    SyncError,
    ConflictError,
)
from .state_tracker import StateTracker
from .frontmatter_parser import FrontmatterParser
from .markdown_syncer import MarkdownSyncer, SyncReport, ConflictResolution

__all__ = [
    "SCHEMA_VERSION",
    "get_schema_path",
    "StateTracker",
    "Story",
    "Epic",
    "Sprint",
    "WorkflowExecution",
    "StateTrackerError",
    "RecordNotFoundError",
    "ValidationError",
    "DatabaseConnectionError",
    "TransactionError",
    "SyncError",
    "ConflictError",
    "FrontmatterParser",
    "MarkdownSyncer",
    "SyncReport",
    "ConflictResolution",
]

SCHEMA_VERSION = 1


def get_schema_path() -> Path:
    """Get path to schema.sql file.

    Returns:
        Path to schema.sql
    """
    return Path(__file__).parent / "schema.sql"
