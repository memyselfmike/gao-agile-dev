"""Migration system for state tracking database."""

from pathlib import Path
from typing import List, Type

__all__ = ["get_all_migrations", "BaseMigration"]


class BaseMigration:
    """Base class for database migrations."""

    version: int = 0
    description: str = ""

    @staticmethod
    def upgrade(db_path: Path) -> bool:
        """Apply migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful
        """
        raise NotImplementedError

    @staticmethod
    def downgrade(db_path: Path) -> bool:
        """Rollback migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful
        """
        raise NotImplementedError


def get_all_migrations() -> List[Type[BaseMigration]]:
    """Get all migration classes in order.

    Returns:
        List of migration classes sorted by version
    """
    from gao_dev.core.state.migrations.migration_001_create_state_schema import (
        Migration001,
    )

    return [Migration001]
