"""Migration 001: Create initial state database schema.

Creates all tables, indexes, triggers, and constraints for the state tracking system.
"""

import sqlite3
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


class Migration001:
    """Create initial state database schema."""

    version = 1
    description = "Create epics, stories, sprints, workflow_executions, state_changes tables"

    @staticmethod
    def upgrade(db_path: Path) -> bool:
        """Apply migration to create schema.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful

        Raises:
            Exception: If migration fails
        """
        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Read schema SQL
                schema_path = Path(__file__).parent.parent / "schema.sql"
                if not schema_path.exists():
                    raise FileNotFoundError(f"Schema file not found: {schema_path}")

                schema_sql = schema_path.read_text(encoding="utf-8")

                # Execute schema creation
                conn.executescript(schema_sql)

                # Create schema_version table if not exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                        description TEXT
                    )
                """)

                # Check if migration already applied
                cursor = conn.execute(
                    "SELECT version FROM schema_version WHERE version = ?",
                    (Migration001.version,),
                )
                if cursor.fetchone():
                    logger.info(
                        "migration_already_applied",
                        version=Migration001.version,
                    )
                    return True

                # Record migration
                conn.execute(
                    """
                    INSERT INTO schema_version (version, description)
                    VALUES (?, ?)
                """,
                    (Migration001.version, Migration001.description),
                )

                conn.commit()

                logger.info(
                    "migration_applied",
                    version=Migration001.version,
                    description=Migration001.description,
                )

                return True

        except Exception as e:
            logger.error(
                "migration_failed", version=Migration001.version, error=str(e)
            )
            raise

    @staticmethod
    def downgrade(db_path: Path) -> bool:
        """Rollback migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful

        Raises:
            Exception: If rollback fails
        """
        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Drop all tables in reverse dependency order
                tables = [
                    "state_changes",
                    "workflow_executions",
                    "story_assignments",
                    "stories",
                    "sprints",
                    "epics",
                ]
                for table in tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")

                # Remove from version table
                conn.execute(
                    "DELETE FROM schema_version WHERE version = ?",
                    (Migration001.version,),
                )

                conn.commit()

                logger.info("migration_rolled_back", version=Migration001.version)
                return True

        except Exception as e:
            logger.error(
                "rollback_failed", version=Migration001.version, error=str(e)
            )
            raise
