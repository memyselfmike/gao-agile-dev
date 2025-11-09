"""
Migration 007: Add Workflow Adjustments Tracking.

This migration creates the workflow_adjustments table to track workflow
adjustments made by the WorkflowAdjuster service based on learnings.

Features:
- Creates workflow_adjustments table to track add/modify/remove adjustments
- Indexes for epic lookup and learning reference
- Foreign key constraints to learning_index and epic_state
- Complete validation and verification

Schema Version: 1.0.6
Created: 2025-11-09
Epic: 29 - Self-Learning Feedback Loop
Story: 29.4 - Workflow Adjustment Logic
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import structlog

logger = structlog.get_logger(__name__)


class Migration007:
    """Workflow adjustments tracking migration."""

    VERSION = "007"
    DESCRIPTION = "Add workflow adjustments tracking table"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: create workflow_adjustments table.

        This migration:
        1. Creates workflow_adjustments table
        2. Creates performance indexes
        3. Records migration in schema_version

        Args:
            conn: SQLite database connection

        Raises:
            sqlite3.Error: If migration fails
        """
        cursor = conn.cursor()

        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            logger.info("migration_007_starting", description=Migration007.DESCRIPTION)

            # Step 1: Create workflow_adjustments table
            logger.info("migration_007_creating_adjustments_table")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    epic_num INTEGER NOT NULL,
                    learning_id INTEGER,
                    adjustment_type TEXT NOT NULL CHECK(adjustment_type IN ('add', 'modify', 'remove')),
                    workflow_name TEXT NOT NULL,
                    reason TEXT,
                    applied_at TEXT NOT NULL,
                    metadata JSON,
                    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE CASCADE,
                    FOREIGN KEY (learning_id) REFERENCES learning_index(id) ON DELETE SET NULL
                )
                """
            )

            logger.info("migration_007_adjustments_table_created")

            # Step 2: Create indexes for performance
            logger.info("migration_007_creating_indexes")

            # Index on epic_num for fast lookup of adjustments per epic
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_adjustments_epic
                ON workflow_adjustments(epic_num)
                """
            )

            # Index on learning_id for tracking which learnings triggered adjustments
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_adjustments_learning
                ON workflow_adjustments(learning_id)
                """
            )

            # Index on adjustment_type for filtering by type
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_adjustments_type
                ON workflow_adjustments(adjustment_type)
                """
            )

            # Index on applied_at for time-based queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_adjustments_applied_at
                ON workflow_adjustments(applied_at DESC)
                """
            )

            # Composite index on epic_num and applied_at for C1 limit enforcement
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_adjustments_epic_time
                ON workflow_adjustments(epic_num, applied_at DESC)
                """
            )

            logger.info(
                "migration_007_indexes_created",
                count=5,
            )

            # Step 3: Record migration
            cursor.execute(
                """
                INSERT OR IGNORE INTO schema_version (version, applied_at, description)
                VALUES (?, datetime('now'), ?)
                """,
                (Migration007.VERSION, Migration007.DESCRIPTION),
            )

            conn.commit()

            logger.info("migration_007_completed", version=Migration007.VERSION)

        except Exception as e:
            logger.error("migration_007_failed", error=str(e))
            conn.rollback()
            raise

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: remove workflow_adjustments table.

        This is straightforward since we're only dropping a table,
        no table rebuild needed.

        Args:
            conn: SQLite database connection

        Raises:
            sqlite3.Error: If rollback fails
        """
        cursor = conn.cursor()

        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            logger.info("migration_007_rollback_starting")

            # Step 1: Drop indexes first
            cursor.execute("DROP INDEX IF EXISTS idx_workflow_adjustments_epic")
            cursor.execute("DROP INDEX IF EXISTS idx_workflow_adjustments_learning")
            cursor.execute("DROP INDEX IF EXISTS idx_workflow_adjustments_type")
            cursor.execute("DROP INDEX IF EXISTS idx_workflow_adjustments_applied_at")
            cursor.execute("DROP INDEX IF EXISTS idx_workflow_adjustments_epic_time")
            logger.info("migration_007_indexes_dropped")

            # Step 2: Drop workflow_adjustments table
            cursor.execute("DROP TABLE IF EXISTS workflow_adjustments")
            logger.info("migration_007_adjustments_table_dropped")

            # Step 3: Remove migration record
            cursor.execute(
                "DELETE FROM schema_version WHERE version = ?",
                (Migration007.VERSION,),
            )

            conn.commit()

            logger.info("migration_007_rollback_completed", version=Migration007.VERSION)

        except Exception as e:
            logger.error("migration_007_rollback_failed", error=str(e))
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
            (Migration007.VERSION,),
        )

        return cursor.fetchone() is not None

    @staticmethod
    def verify(conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Verify migration state.

        This checks:
        1. workflow_adjustments table exists
        2. All columns exist
        3. All indexes exist
        4. Foreign key constraints exist
        5. Migration is recorded

        Args:
            conn: SQLite database connection

        Returns:
            Dictionary with verification results

        Example:
            {
                "applied": True,
                "table_exists": True,
                "columns": ["id", "epic_num", "learning_id", ...],
                "indexes": ["idx_workflow_adjustments_epic", ...],
                "foreign_keys_enabled": True,
                "issues": []
            }
        """
        cursor = conn.cursor()
        result = {
            "applied": False,
            "table_exists": False,
            "columns": [],
            "indexes": [],
            "foreign_keys_enabled": False,
            "issues": [],
        }

        try:
            # Check if migration is recorded
            result["applied"] = Migration007.is_applied(conn)

            if not result["applied"]:
                result["issues"].append("Migration not recorded in schema_version")

            # Check workflow_adjustments table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='workflow_adjustments'
                """
            )
            result["table_exists"] = cursor.fetchone() is not None

            if not result["table_exists"]:
                result["issues"].append("workflow_adjustments table does not exist")
                return result

            # Check columns
            cursor.execute("PRAGMA table_info(workflow_adjustments)")
            columns = [row[1] for row in cursor.fetchall()]

            expected_columns = [
                "id",
                "epic_num",
                "learning_id",
                "adjustment_type",
                "workflow_name",
                "reason",
                "applied_at",
                "metadata",
            ]

            result["columns"] = [col for col in expected_columns if col in columns]

            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                result["issues"].append(
                    f"Missing columns in workflow_adjustments: {missing_columns}"
                )

            # Check indexes
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index'
                """
            )
            all_indexes = [row[0] for row in cursor.fetchall()]

            expected_indexes = [
                "idx_workflow_adjustments_epic",
                "idx_workflow_adjustments_learning",
                "idx_workflow_adjustments_type",
                "idx_workflow_adjustments_applied_at",
                "idx_workflow_adjustments_epic_time",
            ]

            result["indexes"] = [idx for idx in expected_indexes if idx in all_indexes]

            missing_indexes = [idx for idx in expected_indexes if idx not in all_indexes]
            if missing_indexes:
                result["issues"].append(f"Missing indexes: {missing_indexes}")

            # Check foreign keys enabled
            cursor.execute("PRAGMA foreign_keys")
            fk_result = cursor.fetchone()
            result["foreign_keys_enabled"] = fk_result[0] == 1 if fk_result else False

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
        logger.info("migration_007_backup_created", backup=str(backup_path))
        return backup_path
    except Exception as e:
        logger.error("migration_007_backup_failed", error=str(e))
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
            verification = Migration007.verify(conn)
            result["verification"] = verification
            result["success"] = len(verification["issues"]) == 0
            return result

        # Create backup if requested and not dry run
        if backup and not dry_run:
            result["backup_path"] = str(create_backup(db_path))

        # Check current state
        is_applied = Migration007.is_applied(conn)

        if dry_run:
            result["would_apply"] = (direction == "up" and not is_applied) or (
                direction == "down" and is_applied
            )
            result["success"] = True
            return result

        # Apply migration
        if direction == "up":
            if not is_applied:
                print(f"Applying migration {Migration007.VERSION}...")
                Migration007.up(conn)
                print(f"Migration {Migration007.VERSION} applied successfully.")

                # Verify after applying
                verification = Migration007.verify(conn)
                if verification["issues"]:
                    print(f"WARNING: Post-migration verification found issues:")
                    for issue in verification["issues"]:
                        print(f"  - {issue}")
                else:
                    print("Migration verification: PASSED")

                result["success"] = True
            else:
                print(f"Migration {Migration007.VERSION} already applied.")
                result["success"] = True
                result["already_applied"] = True

        elif direction == "down":
            if is_applied:
                print(f"Rolling back migration {Migration007.VERSION}...")
                Migration007.down(conn)
                print(f"Migration {Migration007.VERSION} rolled back successfully.")
                result["success"] = True
            else:
                print(f"Migration {Migration007.VERSION} not applied.")
                result["success"] = True
                result["not_applied"] = True

        return result

    except Exception as e:
        logger.error("migration_007_run_failed", error=str(e), direction=direction)
        result["error"] = str(e)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Migration 007: Workflow Adjustments Tracking"
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
            print(f"Table exists: {verification['table_exists']}")
            print(f"Columns: {len(verification['columns'])}/{8}")
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
