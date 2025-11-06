"""
Migration runner for database schema upgrades.

Provides automatic migration detection, execution, and rollback capabilities
with version tracking through the schema_version table.

Features:
- Automatic detection of pending migrations
- Sequential execution in order
- Rollback support for last N migrations
- Schema version tracking
- Transaction safety with rollback on failure
- Migration logging with timestamps
"""

import sqlite3
import importlib
import inspect
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import structlog

logger = structlog.get_logger(__name__)


class MigrationInfo:
    """Information about a migration."""

    def __init__(
        self,
        version: int,
        name: str,
        module_path: str,
        applied_at: Optional[str] = None
    ):
        self.version = version
        self.name = name
        self.module_path = module_path
        self._applied_at = applied_at

    @property
    def applied_at(self) -> Optional[str]:
        """Get applied_at timestamp."""
        return self._applied_at

    @applied_at.setter
    def applied_at(self, value: Optional[str]) -> None:
        """Set applied_at timestamp."""
        self._applied_at = value

    @property
    def is_applied(self) -> bool:
        """Check if migration is applied (based on applied_at)."""
        return self._applied_at is not None

    def __repr__(self) -> str:
        status = "applied" if self.is_applied else "pending"
        return f"Migration{self.version:03d}({self.name}, {status})"


class MigrationRunner:
    """
    Database migration runner with automatic detection and execution.

    Manages schema upgrades/downgrades through versioned migration files.
    Tracks applied migrations in schema_version table.
    """

    def __init__(self, db_path: Path, migrations_dir: Optional[Path] = None):
        """
        Initialize migration runner.

        Args:
            db_path: Path to SQLite database
            migrations_dir: Directory containing migration files
                           (default: same directory as this file)
        """
        self.db_path = db_path
        if migrations_dir is None:
            self.migrations_dir = Path(__file__).parent
        else:
            self.migrations_dir = migrations_dir

        logger.info(
            "migration_runner_initialized",
            db_path=str(db_path),
            migrations_dir=str(self.migrations_dir)
        )

    def _ensure_schema_version_table(self, conn: sqlite3.Connection) -> None:
        """
        Create schema_version table if it doesn't exist.

        Args:
            conn: Database connection
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT,
                execution_time_ms INTEGER,
                notes TEXT
            )
        """)
        conn.commit()
        logger.debug("schema_version_table_ensured")

    def _get_applied_migrations(self, conn: sqlite3.Connection) -> Dict[int, str]:
        """
        Get list of applied migrations from schema_version table.

        Args:
            conn: Database connection

        Returns:
            Dict mapping version number to applied_at timestamp
        """
        self._ensure_schema_version_table(conn)

        cursor = conn.execute(
            "SELECT version, applied_at FROM schema_version ORDER BY version"
        )
        return {row[0]: row[1] for row in cursor.fetchall()}

    def _discover_migrations(self) -> List[MigrationInfo]:
        """
        Discover all migration files in migrations directory.

        Returns:
            List of MigrationInfo objects sorted by version
        """
        migrations = []

        # Look for migration_XXX_*.py files
        for migration_file in self.migrations_dir.glob("migration_*.py"):
            # Extract version from filename (e.g., migration_003_unify_database.py)
            filename = migration_file.stem
            parts = filename.split("_")

            if len(parts) < 2:
                logger.warning(
                    "migration_invalid_filename",
                    file=migration_file.name,
                    reason="Expected format: migration_XXX_name.py"
                )
                continue

            try:
                version = int(parts[1])
                name = "_".join(parts[2:]) if len(parts) > 2 else "unnamed"

                migrations.append(MigrationInfo(
                    version=version,
                    name=name,
                    module_path=f"gao_dev.core.context.migrations.{filename}"
                ))
            except ValueError:
                logger.warning(
                    "migration_invalid_version",
                    file=migration_file.name,
                    reason="Version must be integer"
                )
                continue

        # Sort by version
        migrations.sort(key=lambda m: m.version)

        logger.debug("migrations_discovered", count=len(migrations))
        return migrations

    def get_migration_status(self) -> List[MigrationInfo]:
        """
        Get status of all migrations (applied and pending).

        Returns:
            List of MigrationInfo objects with applied status
        """
        # Connect to database
        conn = sqlite3.connect(str(self.db_path))
        try:
            applied = self._get_applied_migrations(conn)
        finally:
            conn.close()

        # Discover all migrations
        migrations = self._discover_migrations()

        # Mark applied migrations
        for migration in migrations:
            if migration.version in applied:
                migration.applied_at = applied[migration.version]

        return migrations

    def get_pending_migrations(self) -> List[MigrationInfo]:
        """
        Get list of pending (not yet applied) migrations.

        Returns:
            List of MigrationInfo objects for pending migrations
        """
        all_migrations = self.get_migration_status()
        return [m for m in all_migrations if not m.is_applied]

    def _load_migration_class(self, migration: MigrationInfo) -> Any:
        """
        Load migration class from module.

        Args:
            migration: Migration info

        Returns:
            Migration class

        Raises:
            ImportError: If module cannot be loaded
            AttributeError: If migration class not found
        """
        # Import migration module
        module = importlib.import_module(migration.module_path)

        # Find migration class (e.g., Migration003)
        class_name = f"Migration{migration.version:03d}"

        if not hasattr(module, class_name):
            raise AttributeError(
                f"Migration class '{class_name}' not found in {migration.module_path}"
            )

        return getattr(module, class_name)

    def migrate(self, target_version: Optional[int] = None) -> List[MigrationInfo]:
        """
        Apply pending migrations up to target version.

        Args:
            target_version: Version to migrate to (None = latest)

        Returns:
            List of applied migrations

        Raises:
            Exception: If migration fails
        """
        logger.info("migration_started", target_version=target_version)

        # Get pending migrations
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("migration_no_pending")
            return []

        # Filter by target version
        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]

        if not pending:
            logger.info("migration_already_at_target", target=target_version)
            return []

        logger.info("migration_applying", count=len(pending))

        # Apply each migration
        applied = []
        conn = sqlite3.connect(str(self.db_path))

        try:
            self._ensure_schema_version_table(conn)

            for migration in pending:
                start_time = datetime.now()
                logger.info(
                    "migration_applying_single",
                    version=migration.version,
                    name=migration.name
                )

                # Load migration class
                migration_class = self._load_migration_class(migration)

                # Execute upgrade
                try:
                    # Check if upgrade is a static method or instance method
                    if inspect.ismethod(migration_class.upgrade):
                        # Instance method - create instance
                        instance = migration_class()
                        instance.upgrade(self.db_path)
                    else:
                        # Static method
                        migration_class.upgrade(self.db_path)

                    # Re-ensure schema_version table exists after migration
                    # (in case migration created it or modified schema)
                    conn.close()
                    conn = sqlite3.connect(str(self.db_path))
                    self._ensure_schema_version_table(conn)

                    # Record success
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO schema_version
                        (version, name, applied_at, execution_time_ms)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            migration.version,
                            migration.name,
                            datetime.now().isoformat(),
                            execution_time
                        )
                    )
                    conn.commit()

                    migration.applied_at = datetime.now().isoformat()
                    applied.append(migration)

                    logger.info(
                        "migration_applied",
                        version=migration.version,
                        name=migration.name,
                        execution_time_ms=execution_time
                    )

                except Exception as e:
                    conn.rollback()
                    logger.error(
                        "migration_failed",
                        version=migration.version,
                        name=migration.name,
                        error=str(e)
                    )
                    raise

        finally:
            conn.close()

        logger.info("migration_completed", applied_count=len(applied))
        return applied

    def rollback(self, steps: int = 1) -> List[MigrationInfo]:
        """
        Rollback last N migrations.

        Args:
            steps: Number of migrations to rollback (default: 1)

        Returns:
            List of rolled back migrations

        Raises:
            ValueError: If steps is invalid
            NotImplementedError: If migration doesn't support rollback
        """
        if steps < 1:
            raise ValueError("Steps must be >= 1")

        logger.info("rollback_started", steps=steps)

        # Get applied migrations (in reverse order)
        all_migrations = self.get_migration_status()
        applied = [m for m in all_migrations if m.is_applied]
        applied.reverse()  # Most recent first

        if not applied:
            logger.info("rollback_no_migrations")
            return []

        # Limit to requested steps
        to_rollback = applied[:steps]

        logger.info("rollback_executing", count=len(to_rollback))

        # Rollback each migration
        rolled_back = []
        conn = sqlite3.connect(str(self.db_path))

        try:
            for migration in to_rollback:
                logger.info(
                    "rollback_single",
                    version=migration.version,
                    name=migration.name
                )

                # Load migration class
                migration_class = self._load_migration_class(migration)

                # Check if downgrade exists
                if not hasattr(migration_class, 'downgrade'):
                    raise NotImplementedError(
                        f"Migration {migration.version} does not support rollback"
                    )

                # Execute downgrade
                try:
                    # Check if downgrade is a static method or instance method
                    if inspect.ismethod(migration_class.downgrade):
                        # Instance method
                        instance = migration_class()
                        instance.downgrade(self.db_path)
                    else:
                        # Static method
                        migration_class.downgrade(self.db_path)

                    # Remove from schema_version
                    conn.execute(
                        "DELETE FROM schema_version WHERE version = ?",
                        (migration.version,)
                    )
                    conn.commit()

                    migration.applied_at = None
                    rolled_back.append(migration)

                    logger.info(
                        "rollback_completed_single",
                        version=migration.version,
                        name=migration.name
                    )

                except NotImplementedError:
                    # Migration doesn't support rollback
                    logger.warning(
                        "rollback_not_supported",
                        version=migration.version,
                        name=migration.name
                    )
                    raise

                except Exception as e:
                    conn.rollback()
                    logger.error(
                        "rollback_failed",
                        version=migration.version,
                        name=migration.name,
                        error=str(e)
                    )
                    raise

        finally:
            conn.close()

        logger.info("rollback_completed", rolled_back_count=len(rolled_back))
        return rolled_back

    def get_current_version(self) -> Optional[int]:
        """
        Get current schema version (highest applied migration).

        Returns:
            Current version number, or None if no migrations applied
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            self._ensure_schema_version_table(conn)
            cursor = conn.execute(
                "SELECT MAX(version) FROM schema_version"
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        finally:
            conn.close()

    def validate_migrations(self) -> Tuple[bool, List[str]]:
        """
        Validate migration files for common issues.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        migrations = self._discover_migrations()

        # Check for gaps in version numbers
        versions = [m.version for m in migrations]
        expected_versions = list(range(1, len(versions) + 1))

        missing = set(expected_versions) - set(versions)
        if missing:
            errors.append(f"Missing migration versions: {sorted(missing)}")

        # Check for duplicates
        duplicates = [v for v in versions if versions.count(v) > 1]
        if duplicates:
            errors.append(f"Duplicate migration versions: {sorted(set(duplicates))}")

        # Try to load each migration class
        for migration in migrations:
            try:
                migration_class = self._load_migration_class(migration)

                # Check for upgrade method
                if not hasattr(migration_class, 'upgrade'):
                    errors.append(
                        f"Migration {migration.version} missing 'upgrade' method"
                    )

                # Check upgrade signature
                upgrade_sig = inspect.signature(migration_class.upgrade)
                if 'target_db_path' not in upgrade_sig.parameters:
                    errors.append(
                        f"Migration {migration.version} upgrade() must accept "
                        f"'target_db_path' parameter"
                    )

            except Exception as e:
                errors.append(
                    f"Failed to load migration {migration.version}: {str(e)}"
                )

        is_valid = len(errors) == 0
        return is_valid, errors
