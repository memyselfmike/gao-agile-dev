"""
Unified configuration for GAO-Dev database paths.

This module provides centralized database path configuration to ensure
all components (StateTracker, ContextPersistence, ContextUsageTracker, etc.)
use the same unified database.

All database tables are stored in a single `gao_dev.db` file for:
- Simplified management
- Better foreign key constraints
- Easier migrations
- Consistent backup/restore
"""

from pathlib import Path
from typing import Optional
import os


class DatabaseConfig:
    """
    Centralized database configuration for GAO-Dev.

    Provides unified database path for all components:
    - StateTracker (epics, stories, sprints, workflow_executions)
    - ContextPersistence (workflow_context)
    - ContextUsageTracker (context_usage)
    - ContextLineageTracker (uses context_usage)
    - DocumentRegistry (documents) - Note: Currently separate

    Database location priority:
    1. GAO_DEV_DB_PATH environment variable
    2. Project root / gao_dev.db (default)

    Example:
        >>> config = DatabaseConfig.get_default()
        >>> print(config.db_path)
        /path/to/project/gao_dev.db

        >>> # Use custom path
        >>> config = DatabaseConfig(Path("/custom/path/gao_dev.db"))
        >>> tracker = StateTracker(config.db_path)
    """

    _instance: Optional['DatabaseConfig'] = None

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database configuration.

        Args:
            db_path: Path to unified database file. If None, uses default.
        """
        if db_path is not None:
            self.db_path = Path(db_path)
        else:
            # Check environment variable first
            env_path = os.getenv('GAO_DEV_DB_PATH')
            if env_path:
                self.db_path = Path(env_path)
            else:
                # Default: project root / gao_dev.db
                self.db_path = Path.cwd() / "gao_dev.db"

    @classmethod
    def get_default(cls) -> 'DatabaseConfig':
        """
        Get default database configuration (singleton).

        Returns:
            DatabaseConfig instance with default path
        """
        if cls._instance is None:
            cls._instance = DatabaseConfig()
        return cls._instance

    @classmethod
    def set_default(cls, config: 'DatabaseConfig') -> None:
        """
        Set default database configuration.

        Args:
            config: DatabaseConfig instance to use as default
        """
        cls._instance = config

    @classmethod
    def reset_default(cls) -> None:
        """Reset default configuration (for testing)."""
        cls._instance = None

    def ensure_initialized(self, schema_path: Optional[Path] = None) -> None:
        """
        Ensure database is initialized with schema.

        Creates database file and applies schema if it doesn't exist.

        Args:
            schema_path: Path to SQL schema file. If None, uses default.

        Raises:
            FileNotFoundError: If schema file not found
        """
        if self.db_path.exists():
            return

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize with schema
        from .state.migrations.migration_001_create_state_schema import Migration001
        Migration001.upgrade(self.db_path)

    def __repr__(self) -> str:
        return f"DatabaseConfig(db_path={self.db_path})"


# Convenience functions for backward compatibility

def get_database_path() -> Path:
    """
    Get unified database path.

    Returns:
        Path to gao_dev.db

    Example:
        >>> from gao_dev.core.config import get_database_path
        >>> db_path = get_database_path()
        >>> tracker = StateTracker(db_path)
    """
    return DatabaseConfig.get_default().db_path


def set_database_path(path: Path) -> None:
    """
    Set unified database path.

    Args:
        path: Path to database file

    Example:
        >>> from gao_dev.core.config import set_database_path
        >>> set_database_path(Path("/custom/gao_dev.db"))
    """
    DatabaseConfig.set_default(DatabaseConfig(path))


def get_legacy_state_db_path() -> Path:
    """
    Get path to legacy state database.

    Returns:
        Path to old gao-dev-state.db

    Note:
        This is for migration purposes only. New code should use get_database_path().
    """
    return Path.cwd() / "gao-dev-state.db"


def get_legacy_context_db_path() -> Path:
    """
    Get path to legacy context usage database.

    Returns:
        Path to old .gao/context_usage.db

    Note:
        This is for migration purposes only. New code should use get_database_path().
    """
    return Path.cwd() / ".gao" / "context_usage.db"


def get_documents_db_path() -> Path:
    """
    Get path to documents database.

    Returns:
        Path to .gao-dev/documents.db

    Note:
        Documents DB remains separate for now (Epic 16).
        May be unified in future version.
    """
    gao_dev_dir = Path.cwd() / ".gao-dev"
    gao_dir = Path.cwd() / ".gao"

    # Check both locations for backward compatibility
    if (gao_dev_dir / "documents.db").exists():
        return gao_dev_dir / "documents.db"
    elif (gao_dir / "documents.db").exists():
        return gao_dir / "documents.db"
    else:
        # Default to .gao-dev for new installations
        return gao_dev_dir / "documents.db"
