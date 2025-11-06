"""
Migration 003: Unify all databases into gao_dev.db.

This migration consolidates separate databases (gao-dev-state.db, context_usage.db)
into a single unified gao_dev.db file with proper foreign key constraints.

Features:
- Idempotent (safe to run multiple times)
- Automatic backup of old databases
- Rollback on failure
- Foreign key validation
- Progress reporting
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import structlog

logger = structlog.get_logger(__name__)


class Migration003:
    """Migration to unify all databases into gao_dev.db."""

    @staticmethod
    def upgrade(target_db_path: Path, backup: bool = True) -> None:
        """
        Run migration to unify databases.

        Args:
            target_db_path: Path to target gao_dev.db
            backup: Whether to backup old databases before migration

        Raises:
            sqlite3.Error: If migration fails (with rollback)
        """
        logger.info("migration_003_starting", target=str(target_db_path))

        # Get paths to legacy databases
        legacy_state_db = Path.cwd() / "gao-dev-state.db"
        legacy_context_db = Path.cwd() / ".gao" / "context_usage.db"

        # Check which databases exist
        has_state_db = legacy_state_db.exists()
        has_context_db = legacy_context_db.exists()

        if not has_state_db and not has_context_db:
            logger.info("migration_003_no_legacy_dbs", message="No legacy databases found, nothing to migrate")

        # Ensure target database directory exists
        target_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Load schema SQL
        schema_path = Path(__file__).parent / "003_unify_database.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Migration schema not found: {schema_path}")

        schema_sql = schema_path.read_text(encoding="utf-8")

        # Connect to target database
        conn = None
        try:
            conn = sqlite3.connect(str(target_db_path))
            conn.execute("PRAGMA foreign_keys = OFF")  # Disable during migration

            # Create tables from schema
            logger.info("migration_003_creating_schema")
            conn.executescript(schema_sql)
            conn.commit()

            # Migrate data from legacy databases
            if has_state_db:
                Migration003._migrate_state_db(conn, legacy_state_db)

            if has_context_db:
                Migration003._migrate_context_db(conn, legacy_context_db)

            # Enable foreign keys and validate
            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()

            # Validate foreign key constraints
            logger.info("migration_003_validating_fks")
            violations = Migration003._check_foreign_keys(conn)
            if violations:
                logger.warning("migration_003_fk_violations", count=len(violations))
                for table, violations_list in violations:
                    logger.warning("fk_violation", table=table, violations=violations_list)
            else:
                logger.info("migration_003_fk_validation_passed")

            # Backup legacy databases if requested
            if backup and (has_state_db or has_context_db):
                Migration003._backup_legacy_databases(legacy_state_db, legacy_context_db)

            logger.info("migration_003_completed", target=str(target_db_path))

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error("migration_003_failed", error=str(e))
            raise

        finally:
            if conn:
                conn.close()

    @staticmethod
    def _migrate_state_db(conn: sqlite3.Connection, source_path: Path) -> None:
        """
        Migrate data from legacy gao-dev-state.db.

        Args:
            conn: Target database connection
            source_path: Path to legacy state database
        """
        if not source_path.exists():
            return

        logger.info("migration_003_migrating_state_db", source=str(source_path))

        # Attach source database
        conn.execute(f"ATTACH DATABASE '{source_path}' AS source_state")

        try:
            # Copy tables (only if they don't already have data)
            tables = [
                "epics",
                "stories",
                "sprints",
                "story_assignments",
                "workflow_executions",
                "state_changes"
            ]

            for table in tables:
                # Check if table exists in source
                cursor = conn.execute(
                    "SELECT name FROM source_state.sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
                if not cursor.fetchone():
                    logger.warning("migration_003_table_not_found", table=table, db="source_state")
                    continue

                # Check if target table already has data
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                target_count = cursor.fetchone()[0]

                if target_count > 0:
                    logger.info("migration_003_table_has_data", table=table, count=target_count)
                    continue

                # Copy data
                conn.execute(f"INSERT INTO {table} SELECT * FROM source_state.{table}")
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                migrated_count = cursor.fetchone()[0]
                logger.info("migration_003_table_migrated", table=table, count=migrated_count)

            conn.commit()
            logger.info("migration_003_state_db_migrated")

        finally:
            conn.execute("DETACH DATABASE source_state")

    @staticmethod
    def _migrate_context_db(conn: sqlite3.Connection, source_path: Path) -> None:
        """
        Migrate data from legacy context_usage.db.

        Args:
            conn: Target database connection
            source_path: Path to legacy context usage database
        """
        if not source_path.exists():
            return

        logger.info("migration_003_migrating_context_db", source=str(source_path))

        # Attach source database
        conn.execute(f"ATTACH DATABASE '{source_path}' AS source_context")

        try:
            # Copy workflow_context table
            cursor = conn.execute(
                "SELECT name FROM source_context.sqlite_master WHERE type='table' AND name='workflow_context'"
            )
            if cursor.fetchone():
                # Check if target already has data
                cursor = conn.execute("SELECT COUNT(*) FROM workflow_context")
                target_count = cursor.fetchone()[0]

                if target_count == 0:
                    conn.execute("INSERT INTO workflow_context SELECT * FROM source_context.workflow_context")
                    cursor = conn.execute("SELECT COUNT(*) FROM workflow_context")
                    migrated_count = cursor.fetchone()[0]
                    logger.info("migration_003_table_migrated", table="workflow_context", count=migrated_count)
                else:
                    logger.info("migration_003_table_has_data", table="workflow_context", count=target_count)

            # Copy context_usage table (with schema compatibility check)
            cursor = conn.execute(
                "SELECT name FROM source_context.sqlite_master WHERE type='table' AND name='context_usage'"
            )
            if cursor.fetchone():
                # Check if target already has data
                cursor = conn.execute("SELECT COUNT(*) FROM context_usage")
                target_count = cursor.fetchone()[0]

                if target_count == 0:
                    # Get column names from source table
                    cursor = conn.execute("PRAGMA source_context.table_info(context_usage)")
                    source_columns = [row[1] for row in cursor.fetchall()]

                    # Get column names from target table
                    cursor = conn.execute("PRAGMA table_info(context_usage)")
                    target_columns = [row[1] for row in cursor.fetchall()]

                    # Find common columns
                    common_columns = [col for col in source_columns if col in target_columns]

                    if common_columns:
                        # Build INSERT statement with matching columns only
                        column_list = ", ".join(common_columns)
                        conn.execute(
                            f"INSERT INTO context_usage ({column_list}) "
                            f"SELECT {column_list} FROM source_context.context_usage"
                        )
                        cursor = conn.execute("SELECT COUNT(*) FROM context_usage")
                        migrated_count = cursor.fetchone()[0]
                        logger.info(
                            "migration_003_table_migrated",
                            table="context_usage",
                            count=migrated_count,
                            columns=len(common_columns)
                        )
                    else:
                        logger.warning(
                            "migration_003_schema_incompatible",
                            table="context_usage",
                            message="No common columns found"
                        )
                else:
                    logger.info("migration_003_table_has_data", table="context_usage", count=target_count)

            conn.commit()
            logger.info("migration_003_context_db_migrated")

        finally:
            conn.execute("DETACH DATABASE source_context")

    @staticmethod
    def _check_foreign_keys(conn: sqlite3.Connection) -> List[Tuple[str, List[dict]]]:
        """
        Check for foreign key violations.

        Args:
            conn: Database connection

        Returns:
            List of (table_name, violations) tuples
        """
        conn.execute("PRAGMA foreign_keys = ON")

        # Get all tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        violations = []
        for table in tables:
            cursor = conn.execute(f"PRAGMA foreign_key_check({table})")
            table_violations = cursor.fetchall()
            if table_violations:
                violations.append((table, table_violations))

        return violations

    @staticmethod
    def _backup_legacy_databases(
        state_db: Path,
        context_db: Path,
        backup_dir: Optional[Path] = None
    ) -> None:
        """
        Backup legacy databases before migration.

        Args:
            state_db: Path to legacy state database
            context_db: Path to legacy context database
            backup_dir: Directory for backups (default: .gao/backups/)
        """
        if backup_dir is None:
            backup_dir = Path.cwd() / ".gao" / "backups"

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if state_db.exists():
            backup_path = backup_dir / f"gao-dev-state_{timestamp}.db"
            shutil.copy2(state_db, backup_path)
            logger.info("migration_003_backup_created", original=str(state_db), backup=str(backup_path))

        if context_db.exists():
            backup_path = backup_dir / f"context_usage_{timestamp}.db"
            shutil.copy2(context_db, backup_path)
            logger.info("migration_003_backup_created", original=str(context_db), backup=str(backup_path))

    @staticmethod
    def downgrade(target_db_path: Path) -> None:
        """
        Downgrade migration (not implemented).

        For this migration, downgrade would require:
        1. Extracting tables back to separate databases
        2. Removing foreign key constraints
        3. Restoring legacy database structure

        This is intentionally not implemented as the unified database
        provides significant benefits and reverting is complex.

        Args:
            target_db_path: Path to gao_dev.db

        Raises:
            NotImplementedError: Always raised
        """
        raise NotImplementedError(
            "Migration 003 downgrade not supported. "
            "Restore from backup if needed."
        )


def run_migration(target_db_path: Optional[Path] = None, backup: bool = True) -> None:
    """
    Run migration 003 (convenience function).

    Args:
        target_db_path: Path to target database (default: ./gao_dev.db)
        backup: Whether to backup legacy databases
    """
    if target_db_path is None:
        target_db_path = Path.cwd() / "gao_dev.db"

    Migration003.upgrade(target_db_path, backup=backup)


if __name__ == "__main__":
    # CLI support for running migration directly
    import sys

    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = Path.cwd() / "gao_dev.db"

    run_migration(target_path)
