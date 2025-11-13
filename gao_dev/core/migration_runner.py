"""
Migration Runner with Transaction Safety

Manages database migrations with transaction safety and automatic rollback.

Story 36.9: Migration Transaction Safety
"""

import sqlite3
import structlog
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable

from gao_dev.core.backup_manager import BackupManager


logger = structlog.get_logger(__name__)


@dataclass
class Migration:
    """
    Represents a database migration.

    Attributes:
        version: Migration version number (e.g., 1, 2, 3)
        description: Human-readable description
        up: Function to apply migration (takes sqlite3.Connection)
        down: Optional function to rollback migration (takes sqlite3.Connection)
    """

    version: int
    description: str
    up: Callable[[sqlite3.Connection], None]
    down: Optional[Callable[[sqlite3.Connection], None]] = None


class MigrationRunner:
    """
    Run database migrations with transaction safety.

    Responsibilities:
    - Create backup before migrations
    - Track applied migrations in schema_version table
    - Execute migrations within transactions
    - Rollback on error and restore backup
    - Support both forward (up) and rollback (down) migrations
    """

    def __init__(self, project_path: Path):
        """
        Initialize migration runner.

        Args:
            project_path: Path to user project directory
        """
        self.project_path = project_path
        self.gaodev_dir = project_path / ".gao-dev"
        self.db_path = self.gaodev_dir / "documents.db"
        self.backup_manager = BackupManager()
        self.logger = logger.bind(component="MigrationRunner")

    def initialize_schema_version_table(self) -> None:
        """
        Create schema_version table if it doesn't exist.

        Table schema:
            version INTEGER PRIMARY KEY - Migration version number
            description TEXT - Migration description
            applied_at TEXT - ISO timestamp when migration was applied
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
            self.logger.info("schema_version_table_initialized")

        except Exception as e:
            self.logger.error("failed_to_initialize_schema_version", error=str(e))
            raise

        finally:
            conn.close()

    def get_current_version(self) -> int:
        """
        Get current schema version from database.

        Returns:
            Current version number (0 if no migrations applied)
        """
        if not self.db_path.exists():
            return 0

        conn = sqlite3.connect(self.db_path)
        try:
            # Check if schema_version table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if cursor.fetchone() is None:
                return 0

            # Get max version
            cursor = conn.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            version = result[0] if result[0] is not None else 0

            self.logger.info("current_schema_version", version=version)
            return version

        except Exception as e:
            self.logger.error("failed_to_get_current_version", error=str(e))
            raise

        finally:
            conn.close()

    def get_applied_migrations(self) -> List[int]:
        """
        Get list of applied migration versions.

        Returns:
            List of version numbers, sorted ascending
        """
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)
        try:
            # Check if schema_version table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            if cursor.fetchone() is None:
                return []

            cursor = conn.execute("SELECT version FROM schema_version ORDER BY version ASC")
            versions = [row[0] for row in cursor.fetchall()]

            return versions

        except Exception as e:
            self.logger.error("failed_to_get_applied_migrations", error=str(e))
            raise

        finally:
            conn.close()

    def run_migrations(self, migrations: List[Migration]) -> None:
        """
        Run all pending migrations within a transaction.

        Applies only migrations with version > current_version.
        If any migration fails, rolls back transaction and restores backup.

        Args:
            migrations: List of Migration objects to apply

        Raises:
            Exception: If migration fails (after rollback and restore)
        """
        # Initialize schema_version table
        self.initialize_schema_version_table()

        # Get current version
        current_version = self.get_current_version()

        # Filter pending migrations
        pending = [m for m in migrations if m.version > current_version]

        if not pending:
            self.logger.info("no_pending_migrations", current_version=current_version)
            return

        # Sort by version
        pending.sort(key=lambda m: m.version)

        self.logger.info(
            "running_migrations",
            current_version=current_version,
            target_version=pending[-1].version,
            migration_count=len(pending),
        )

        # Create backup before migrations
        backup_path = None
        try:
            backup_path = self.backup_manager.create_backup(
                self.project_path, reason="pre_migration"
            )
            self.logger.info("backup_created_for_migration", backup_path=str(backup_path))

        except Exception as e:
            self.logger.error("backup_failed", error=str(e))
            raise Exception(f"Failed to create backup before migration: {e}")

        # Run migrations in transaction
        conn = sqlite3.connect(self.db_path)
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")

            for migration in pending:
                self.logger.info(
                    "applying_migration",
                    version=migration.version,
                    description=migration.description,
                )

                # Apply migration
                migration.up(conn)

                # Record migration
                conn.execute(
                    """
                    INSERT INTO schema_version (version, description, applied_at)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (migration.version, migration.description),
                )

                self.logger.info("migration_applied", version=migration.version)

            # Commit transaction
            conn.commit()

            self.logger.info(
                "migrations_completed",
                new_version=pending[-1].version,
                migrations_applied=len(pending),
            )

        except Exception as e:
            # Rollback transaction
            self.logger.error(
                "migration_failed_rolling_back",
                error=str(e),
                current_version=current_version,
            )

            try:
                conn.rollback()
                self.logger.info("transaction_rolled_back")

            except Exception as rollback_error:
                self.logger.error("rollback_failed", error=str(rollback_error))

            # Close connection BEFORE restoring backup
            conn.close()

            # Restore from backup
            if backup_path:
                try:
                    self.logger.info("restoring_backup", backup_path=str(backup_path))
                    self.backup_manager.restore_backup(self.project_path, backup_path)
                    self.logger.info("backup_restored")

                except Exception as restore_error:
                    self.logger.error("restore_failed", error=str(restore_error))
                    raise Exception(
                        f"Migration failed AND backup restore failed: {e}\n"
                        f"Restore error: {restore_error}"
                    )

            raise Exception(f"Migration failed and was rolled back: {e}")

        finally:
            # Ensure connection is closed (may already be closed in except block)
            try:
                conn.close()
            except Exception:
                pass  # Already closed

    def rollback_migration(self, target_version: int, migrations: List[Migration]) -> None:
        """
        Rollback to a specific version.

        Applies down() migrations in reverse order.

        Args:
            target_version: Version to rollback to
            migrations: List of all Migration objects (must have down() defined)

        Raises:
            ValueError: If down() not defined for migrations being rolled back
            Exception: If rollback fails
        """
        current_version = self.get_current_version()

        if target_version >= current_version:
            self.logger.info("no_rollback_needed", current_version=current_version)
            return

        # Get migrations to rollback (reverse order)
        applied = self.get_applied_migrations()
        to_rollback = [v for v in applied if v > target_version]
        to_rollback.sort(reverse=True)

        if not to_rollback:
            self.logger.info("no_migrations_to_rollback")
            return

        self.logger.info(
            "rolling_back_migrations",
            current_version=current_version,
            target_version=target_version,
            rollback_count=len(to_rollback),
        )

        # Create backup before rollback
        backup_path = None
        try:
            backup_path = self.backup_manager.create_backup(
                self.project_path, reason="pre_rollback"
            )

        except Exception as e:
            self.logger.error("backup_failed", error=str(e))
            raise Exception(f"Failed to create backup before rollback: {e}")

        # Create migration lookup and validate
        migration_map = {m.version: m for m in migrations}

        # Validate all migrations have down() BEFORE starting transaction
        for version in to_rollback:
            migration = migration_map.get(version)

            if not migration:
                raise ValueError(f"Migration {version} not found in migration list")

            if not migration.down:
                raise ValueError(f"Migration {version} has no down() function defined")

        # Run rollback in transaction
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("BEGIN TRANSACTION")

            for version in to_rollback:
                migration = migration_map[version]

                self.logger.info("rolling_back_migration", version=version)

                # Apply rollback
                migration.down(conn)

                # Remove from schema_version
                conn.execute("DELETE FROM schema_version WHERE version = ?", (version,))

                self.logger.info("migration_rolled_back", version=version)

            conn.commit()

            self.logger.info(
                "rollback_completed",
                new_version=target_version,
                migrations_rolled_back=len(to_rollback),
            )

        except Exception as e:
            self.logger.error("rollback_failed", error=str(e))

            try:
                conn.rollback()
            except Exception as rollback_error:
                self.logger.error("transaction_rollback_failed", error=str(rollback_error))

            # Close connection BEFORE restoring backup
            conn.close()

            # Restore backup
            if backup_path:
                try:
                    self.backup_manager.restore_backup(self.project_path, backup_path)
                    self.logger.info("backup_restored_after_failed_rollback")

                except Exception as restore_error:
                    self.logger.error("restore_failed", error=str(restore_error))

            raise Exception(f"Rollback failed: {e}")

        finally:
            # Ensure connection is closed (may already be closed in except block)
            try:
                conn.close()
            except Exception:
                pass  # Already closed
