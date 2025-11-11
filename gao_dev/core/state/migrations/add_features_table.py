"""Migration 002: Add features table with triggers and audit trail.

Creates features table, indexes, audit trail, and triggers for the
feature-based document structure system.

Epic: 34 - Integration & Variables
Story: 34.1 - Schema Migration
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


class AddFeaturesTableMigration:
    """
    Migration to add features table and related infrastructure.

    Features:
    - Creates features table with CHECK constraints
    - Creates indexes for performance
    - Creates triggers (auto-timestamps, audit trail)
    - Creates features_audit table
    - Idempotent (safe to run multiple times)
    """

    VERSION = "002_add_features_table"

    def __init__(self, db_path: Path):
        """
        Initialize migration.

        Args:
            db_path: Path to documents.db
        """
        self.db_path = db_path

    def apply(self) -> bool:
        """
        Apply migration.

        Returns:
            True if migration applied, False if already applied

        Raises:
            RuntimeError: If migration fails
        """
        logger.info("Applying features table migration", db_path=str(self.db_path))

        # Check if migration already applied
        if self._is_applied():
            logger.info("Migration already applied, skipping")
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Create features table
                self._create_features_table(conn)

                # Create indexes
                self._create_indexes(conn)

                # Create audit table
                self._create_audit_table(conn)

                # Create triggers
                self._create_triggers(conn)

                # Record migration
                self._record_migration(conn)

                conn.commit()

            logger.info("Migration applied successfully")
            return True

        except Exception as e:
            logger.error("Migration failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Migration failed: {str(e)}") from e

    def rollback(self) -> bool:
        """
        Rollback migration.

        Returns:
            True if rolled back, False if not applied

        Raises:
            RuntimeError: If rollback fails
        """
        logger.info("Rolling back features table migration", db_path=str(self.db_path))

        if not self._is_applied():
            logger.info("Migration not applied, nothing to rollback")
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Drop triggers
                conn.execute("DROP TRIGGER IF EXISTS features_completed_at_update")
                conn.execute("DROP TRIGGER IF EXISTS features_audit_insert")
                conn.execute("DROP TRIGGER IF EXISTS features_audit_update")
                conn.execute("DROP TRIGGER IF EXISTS features_audit_delete")

                # Drop tables
                conn.execute("DROP TABLE IF EXISTS features_audit")
                conn.execute("DROP TABLE IF EXISTS features")

                # Remove migration record
                conn.execute(
                    "DELETE FROM migrations WHERE version = ?",
                    (self.VERSION,)
                )

                conn.commit()

            logger.info("Migration rolled back successfully")
            return True

        except Exception as e:
            logger.error("Rollback failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Rollback failed: {str(e)}") from e

    def _is_applied(self) -> bool:
        """Check if migration already applied."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if migrations table exists
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'"
            ).fetchone()

            if not result:
                # Create migrations table
                conn.execute("""
                    CREATE TABLE migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT UNIQUE NOT NULL,
                        applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                conn.commit()
                return False

            # Check if this migration applied
            result = conn.execute(
                "SELECT version FROM migrations WHERE version = ?",
                (self.VERSION,)
            ).fetchone()

            return result is not None

    def _create_features_table(self, conn: sqlite3.Connection) -> None:
        """Create features table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
                status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
                scale_level INTEGER NOT NULL CHECK(scale_level >= 0 AND scale_level <= 4),
                description TEXT,
                owner TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT,
                metadata JSON
            )
        """)
        logger.info("Created features table")

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create indexes for performance."""
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scope ON features(scope)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_status ON features(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scale_level ON features(scale_level)")
        logger.info("Created indexes")

    def _create_audit_table(self, conn: sqlite3.Connection) -> None:
        """Create audit trail table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS features_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER NOT NULL,
                operation TEXT NOT NULL CHECK(operation IN ('INSERT', 'UPDATE', 'DELETE')),
                old_value JSON,
                new_value JSON,
                changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                changed_by TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_audit_feature_id ON features_audit(feature_id)")
        logger.info("Created audit table")

    def _create_triggers(self, conn: sqlite3.Connection) -> None:
        """Create database triggers."""

        # Trigger 1: Auto-set completed_at when status becomes 'complete'
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_completed_at_update
            AFTER UPDATE OF status ON features
            FOR EACH ROW
            WHEN NEW.status = 'complete' AND OLD.status != 'complete'
            BEGIN
                UPDATE features SET completed_at = datetime('now') WHERE id = NEW.id;
            END
        """)

        # Trigger 3: Audit INSERT
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_audit_insert
            AFTER INSERT ON features
            FOR EACH ROW
            BEGIN
                INSERT INTO features_audit (feature_id, operation, new_value, changed_at)
                VALUES (
                    NEW.id,
                    'INSERT',
                    json_object(
                        'name', NEW.name,
                        'scope', NEW.scope,
                        'status', NEW.status,
                        'scale_level', NEW.scale_level,
                        'description', NEW.description,
                        'owner', NEW.owner
                    ),
                    datetime('now')
                );
            END
        """)

        # Trigger 4: Audit UPDATE
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_audit_update
            AFTER UPDATE ON features
            FOR EACH ROW
            BEGIN
                INSERT INTO features_audit (feature_id, operation, old_value, new_value, changed_at)
                VALUES (
                    NEW.id,
                    'UPDATE',
                    json_object(
                        'name', OLD.name,
                        'scope', OLD.scope,
                        'status', OLD.status,
                        'scale_level', OLD.scale_level,
                        'description', OLD.description,
                        'owner', OLD.owner
                    ),
                    json_object(
                        'name', NEW.name,
                        'scope', NEW.scope,
                        'status', NEW.status,
                        'scale_level', NEW.scale_level,
                        'description', NEW.description,
                        'owner', NEW.owner
                    ),
                    datetime('now')
                );
            END
        """)

        # Trigger 5: Audit DELETE
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_audit_delete
            AFTER DELETE ON features
            FOR EACH ROW
            BEGIN
                INSERT INTO features_audit (feature_id, operation, old_value, changed_at)
                VALUES (
                    OLD.id,
                    'DELETE',
                    json_object(
                        'name', OLD.name,
                        'scope', OLD.scope,
                        'status', OLD.status,
                        'scale_level', OLD.scale_level,
                        'description', OLD.description,
                        'owner', OLD.owner
                    ),
                    datetime('now')
                );
            END
        """)

        logger.info("Created triggers")

    def _record_migration(self, conn: sqlite3.Connection) -> None:
        """Record migration as applied."""
        conn.execute(
            "INSERT INTO migrations (version, applied_at) VALUES (?, datetime('now'))",
            (self.VERSION,)
        )
        logger.info("Recorded migration", version=self.VERSION)


class Migration002:
    """Migration wrapper for registry compatibility."""

    version = 2
    description = "Add features table with triggers and audit trail"

    @staticmethod
    def upgrade(db_path: Path) -> bool:
        """Apply migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful
        """
        migration = AddFeaturesTableMigration(db_path)
        return migration.apply()

    @staticmethod
    def downgrade(db_path: Path) -> bool:
        """Rollback migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful
        """
        migration = AddFeaturesTableMigration(db_path)
        return migration.rollback()
