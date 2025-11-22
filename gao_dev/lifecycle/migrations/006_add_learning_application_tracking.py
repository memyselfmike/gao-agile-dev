"""
Migration 006: Add Learning Application Tracking.

This migration enhances the learning_index table with application tracking metrics
and creates a new learning_applications table to track when learnings are applied.

Features:
- Adds application tracking columns to learning_index table
- Creates learning_applications table to track outcomes
- Implements table rebuild strategy for rollback (C6 fix)
- Automatic database backup before migration
- Complete validation and verification

Schema Version: 1.0.5
Created: 2025-11-09
Epic: 29 - Self-Learning Feedback Loop
Story: 29.1 - Learning Schema Enhancement
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import structlog

logger = structlog.get_logger(__name__)


class Migration006:
    """Learning application tracking migration."""

    VERSION = "006"
    DESCRIPTION = "Add learning application tracking with metrics and outcomes"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: enhance learning_index and create learning_applications table.

        This migration:
        1. Adds application tracking columns to learning_index
        2. Creates learning_applications table
        3. Creates performance indexes
        4. Records migration in schema_version

        Args:
            conn: SQLite database connection

        Raises:
            sqlite3.Error: If migration fails
        """
        cursor = conn.cursor()

        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            logger.info("migration_006_starting", description=Migration006.DESCRIPTION)

            # Step 1: Add new columns to learning_index table
            # Note: SQLite supports ALTER TABLE ADD COLUMN in 3.35+
            logger.info("migration_006_adding_columns")

            cursor.execute(
                """
                ALTER TABLE learning_index
                ADD COLUMN application_count INTEGER DEFAULT 0
                """
            )

            cursor.execute(
                """
                ALTER TABLE learning_index
                ADD COLUMN success_rate REAL DEFAULT 1.0
                """
            )

            cursor.execute(
                """
                ALTER TABLE learning_index
                ADD COLUMN confidence_score REAL DEFAULT 0.5
                """
            )

            cursor.execute(
                """
                ALTER TABLE learning_index
                ADD COLUMN decay_factor REAL DEFAULT 1.0
                """
            )

            logger.info(
                "migration_006_columns_added",
                columns=["application_count", "success_rate", "confidence_score", "decay_factor"],
            )

            # Step 2: Create learning_applications table
            logger.info("migration_006_creating_applications_table")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    learning_id INTEGER NOT NULL,
                    epic_num INTEGER,
                    story_num INTEGER,
                    outcome TEXT NOT NULL CHECK(outcome IN ('success', 'failure', 'partial')),
                    application_context TEXT,
                    applied_at TEXT NOT NULL,
                    metadata JSON,
                    FOREIGN KEY (learning_id) REFERENCES learning_index(id) ON DELETE CASCADE,
                    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE SET NULL
                )
                """
            )

            logger.info("migration_006_applications_table_created")

            # Step 3: Create indexes for performance
            logger.info("migration_006_creating_indexes")

            # Index on learning_id for fast lookup of applications
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_applications_learning_id
                ON learning_applications(learning_id)
                """
            )

            # Index on epic_num for filtering by epic
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_applications_epic
                ON learning_applications(epic_num)
                """
            )

            # Index on applied_at for time-based queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_applications_applied_at
                ON learning_applications(applied_at DESC)
                """
            )

            # Composite index on category and is_active for learning search
            # (C6 gap analysis)
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_index_category_active
                ON learning_index(category, is_active)
                """
            )

            # Index on relevance_score for sorting
            # (C6 gap analysis)
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_index_relevance
                ON learning_index(relevance_score DESC)
                """
            )

            logger.info(
                "migration_006_indexes_created",
                count=5,
            )

            # Step 4: Record migration
            cursor.execute(
                """
                INSERT OR IGNORE INTO schema_version (version, applied_at, description)
                VALUES (?, datetime('now'), ?)
                """,
                (Migration006.VERSION, Migration006.DESCRIPTION),
            )

            conn.commit()

            logger.info("migration_006_completed", version=Migration006.VERSION)

        except Exception as e:
            logger.error("migration_006_failed", error=str(e))
            conn.rollback()
            raise

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: remove learning_applications table and new columns.

        This uses table rebuild strategy (C6 fix) because SQLite doesn't support
        DROP COLUMN directly. The process:
        1. Create temporary table with old schema
        2. Copy data (excluding new columns)
        3. Drop original table
        4. Rename temporary table
        5. Recreate indexes

        Args:
            conn: SQLite database connection

        Raises:
            sqlite3.Error: If rollback fails
        """
        cursor = conn.cursor()

        try:
            # Disable foreign keys during table rebuild
            cursor.execute("PRAGMA foreign_keys = OFF")

            logger.info("migration_006_rollback_starting")

            # Step 1: Drop learning_applications table
            cursor.execute("DROP TABLE IF EXISTS learning_applications")
            logger.info("migration_006_applications_table_dropped")

            # Step 2: Drop indexes that we added
            cursor.execute("DROP INDEX IF EXISTS idx_learning_index_category_active")
            cursor.execute("DROP INDEX IF EXISTS idx_learning_index_relevance")
            logger.info("migration_006_indexes_dropped")

            # Step 3: Rebuild learning_index table without new columns
            # This is the C6 fix - table rebuild strategy
            logger.info("migration_006_rebuilding_learning_index")

            # Create temporary table with old schema
            cursor.execute(
                """
                CREATE TABLE learning_index_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    category TEXT NOT NULL CHECK(category IN (
                        'technical', 'process', 'domain', 'architectural', 'team'
                    )),
                    learning TEXT NOT NULL,
                    context TEXT,
                    source_type TEXT CHECK(source_type IN (
                        'retrospective', 'postmortem', 'code_review', 'incident', 'experiment'
                    )),
                    epic_num INTEGER,
                    story_num INTEGER,
                    relevance_score REAL DEFAULT 1.0,
                    superseded_by INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    indexed_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata JSON,
                    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE SET NULL,
                    FOREIGN KEY (superseded_by) REFERENCES learning_index(id) ON DELETE SET NULL
                )
                """
            )

            # Copy data from original table (excluding new columns)
            cursor.execute(
                """
                INSERT INTO learning_index_temp (
                    id, topic, category, learning, context, source_type,
                    epic_num, story_num, relevance_score, superseded_by,
                    is_active, indexed_at, created_at, metadata
                )
                SELECT
                    id, topic, category, learning, context, source_type,
                    epic_num, story_num, relevance_score, superseded_by,
                    is_active, indexed_at, created_at, metadata
                FROM learning_index
                """
            )

            # Drop original table
            cursor.execute("DROP TABLE learning_index")

            # Rename temp table to original name
            cursor.execute("ALTER TABLE learning_index_temp RENAME TO learning_index")

            logger.info("migration_006_learning_index_rebuilt")

            # Step 4: Recreate original indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_topic ON learning_index(topic)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_category ON learning_index(category)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_active ON learning_index(is_active)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_relevance ON learning_index(relevance_score DESC)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_learning_active_category "
                "ON learning_index(is_active, category, relevance_score DESC)"
            )

            logger.info("migration_006_original_indexes_recreated")

            # Step 5: Remove migration record
            cursor.execute(
                "DELETE FROM schema_version WHERE version = ?",
                (Migration006.VERSION,),
            )

            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            conn.commit()

            logger.info("migration_006_rollback_completed", version=Migration006.VERSION)

        except Exception as e:
            logger.error("migration_006_rollback_failed", error=str(e))
            conn.rollback()
            raise

    @staticmethod
    def is_applied(conn: sqlite3.Connection) -> bool:
        """
        Check if this migration has been applied.

        Args:
            conn: SQLite database connection

        Returns:
            True if migration is applied, False otherwise
        """
        cursor = conn.cursor()

        # Check if schema_version table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='schema_version'
            """
        )

        if not cursor.fetchone():
            return False

        # Check if this version is recorded
        cursor.execute(
            "SELECT version FROM schema_version WHERE version = ?",
            (Migration006.VERSION,),
        )

        return cursor.fetchone() is not None

    @staticmethod
    def verify(conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Verify migration state.

        This checks:
        1. All new columns exist in learning_index
        2. learning_applications table exists
        3. All indexes exist
        4. Foreign key constraints work
        5. Migration is recorded

        Args:
            conn: SQLite database connection

        Returns:
            Dictionary with verification results

        Example:
            {
                "applied": True,
                "learning_index_columns": ["application_count", "success_rate", ...],
                "learning_applications_exists": True,
                "indexes": ["idx_learning_applications_learning_id", ...],
                "foreign_keys_enabled": True,
                "issues": []
            }
        """
        cursor = conn.cursor()
        result = {
            "applied": False,
            "learning_index_columns": [],
            "learning_applications_exists": False,
            "indexes": [],
            "foreign_keys_enabled": False,
            "issues": [],
        }

        try:
            # Check if migration is recorded
            result["applied"] = Migration006.is_applied(conn)

            if not result["applied"]:
                result["issues"].append("Migration not recorded in schema_version")

            # Check learning_index columns
            cursor.execute("PRAGMA table_info(learning_index)")
            columns = [row[1] for row in cursor.fetchall()]

            expected_columns = [
                "application_count",
                "success_rate",
                "confidence_score",
                "decay_factor",
            ]

            result["learning_index_columns"] = [
                col for col in expected_columns if col in columns
            ]

            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                result["issues"].append(
                    f"Missing columns in learning_index: {missing_columns}"
                )

            # Check learning_applications table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='learning_applications'
                """
            )
            result["learning_applications_exists"] = cursor.fetchone() is not None

            if not result["learning_applications_exists"]:
                result["issues"].append("learning_applications table does not exist")

            # Check indexes
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index'
                """
            )
            all_indexes = [row[0] for row in cursor.fetchall()]

            expected_indexes = [
                "idx_learning_applications_learning_id",
                "idx_learning_applications_epic",
                "idx_learning_applications_applied_at",
                "idx_learning_index_category_active",
                "idx_learning_index_relevance",
            ]

            result["indexes"] = [idx for idx in expected_indexes if idx in all_indexes]

            missing_indexes = [idx for idx in expected_indexes if idx not in all_indexes]
            if missing_indexes:
                result["issues"].append(f"Missing indexes: {missing_indexes}")

            # Check foreign keys enabled
            # Note: PRAGMA foreign_keys is session-specific, not persisted
            # This check is informational only, not an error
            cursor.execute("PRAGMA foreign_keys")
            fk_result = cursor.fetchone()
            result["foreign_keys_enabled"] = fk_result[0] == 1 if fk_result else False

            # Don't treat disabled foreign keys as an issue since it's session-specific
            # Users must enable it themselves in their connections

        except Exception as e:
            result["issues"].append(f"Verification error: {str(e)}")

        return result


def create_backup(db_path: Path) -> Path:
    """
    Create backup of database before migration.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file

    Raises:
        IOError: If backup fails
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"

    try:
        shutil.copy2(db_path, backup_path)
        logger.info("migration_006_backup_created", backup=str(backup_path))
        return backup_path
    except Exception as e:
        logger.error("migration_006_backup_failed", error=str(e))
        raise


def run_migration(
    db_path: Path,
    direction: str = "up",
    backup: bool = True,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Run migration on specified database.

    Args:
        db_path: Path to SQLite database file
        direction: 'up' to apply, 'down' to rollback, 'verify' to check state
        backup: Whether to create backup before migration (default: True)
        dry_run: If True, only verify without making changes

    Returns:
        Dictionary with migration results

    Raises:
        ValueError: If direction is invalid
        FileNotFoundError: If database file doesn't exist
    """
    if direction not in ["up", "down", "verify"]:
        raise ValueError(
            f"Invalid direction: {direction}. Must be 'up', 'down', or 'verify'."
        )

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    result = {
        "direction": direction,
        "db_path": str(db_path),
        "backup_path": None,
        "success": False,
        "dry_run": dry_run,
    }

    conn = sqlite3.connect(str(db_path))

    try:
        if direction == "verify":
            # Just verify current state
            verification = Migration006.verify(conn)
            result["verification"] = verification
            result["success"] = len(verification["issues"]) == 0
            return result

        # Create backup if requested and not dry run
        if backup and not dry_run:
            result["backup_path"] = str(create_backup(db_path))

        # Check current state
        is_applied = Migration006.is_applied(conn)

        if dry_run:
            result["would_apply"] = (direction == "up" and not is_applied) or (
                direction == "down" and is_applied
            )
            result["success"] = True
            return result

        # Apply migration
        if direction == "up":
            if not is_applied:
                print(f"Applying migration {Migration006.VERSION}...")
                Migration006.up(conn)
                print(f"Migration {Migration006.VERSION} applied successfully.")

                # Verify after applying
                verification = Migration006.verify(conn)
                if verification["issues"]:
                    print("WARNING: Post-migration verification found issues:")
                    for issue in verification["issues"]:
                        print(f"  - {issue}")
                else:
                    print("Migration verification: PASSED")

                result["success"] = True
            else:
                print(f"Migration {Migration006.VERSION} already applied.")
                result["success"] = True
                result["already_applied"] = True

        elif direction == "down":
            if is_applied:
                print(f"Rolling back migration {Migration006.VERSION}...")
                Migration006.down(conn)
                print(f"Migration {Migration006.VERSION} rolled back successfully.")
                result["success"] = True
            else:
                print(f"Migration {Migration006.VERSION} not applied.")
                result["success"] = True
                result["not_applied"] = True

        return result

    except Exception as e:
        logger.error("migration_006_run_failed", error=str(e), direction=direction)
        result["error"] = str(e)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Migration 006: Learning Application Tracking"
    )
    parser.add_argument("db_path", type=Path, help="Path to database file")
    parser.add_argument(
        "direction",
        nargs="?",
        default="up",
        choices=["up", "down", "verify"],
        help="Migration direction (default: up)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify without making changes",
    )

    args = parser.parse_args()

    try:
        result = run_migration(
            db_path=args.db_path,
            direction=args.direction,
            backup=not args.no_backup,
            dry_run=args.dry_run,
        )

        if args.direction == "verify":
            print("\n=== Verification Results ===")
            verification = result["verification"]
            print(f"Migration applied: {verification['applied']}")
            print(f"New columns: {verification['learning_index_columns']}")
            print(f"Applications table exists: {verification['learning_applications_exists']}")
            print(f"Indexes created: {len(verification['indexes'])}/{5}")
            print(f"Foreign keys enabled: {verification['foreign_keys_enabled']}")

            if verification["issues"]:
                print("\nISSUES FOUND:")
                for issue in verification["issues"]:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("\nVerification: PASSED")

        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
