"""
Tests for Migration 005: State Tracking Tables.

Epic: 24 - State Tables & Tracker
Story: 24.1 - Create Migration 005 (State Tables)
"""

import sqlite3
import tempfile
from pathlib import Path
import importlib.util
import sys

import pytest


def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = Path(__file__).parent.parent.parent.parent / "gao_dev" / "lifecycle" / "migrations" / "005_add_state_tables.py"
    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_005"] = module
    spec.loader.exec_module(module)
    return module.Migration005


Migration005 = load_migration_005()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_with_schema_version(temp_db):
    """Create a database with schema_version table."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    # Create schema_version table (from migration 001)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
        """
    )

    # Create epic_state table for foreign key dependencies
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS epic_state_temp (
            epic_num INTEGER PRIMARY KEY
        )
        """
    )

    conn.commit()
    conn.close()

    return temp_db


class TestMigration005Up:
    """Tests for migration up (applying)."""

    def test_creates_all_five_tables(self, db_with_schema_version):
        """Test that migration creates all 5 state tracking tables."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            Migration005.up(conn)

            cursor = conn.cursor()

            # Check all 5 tables exist
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN (
                    'epic_state', 'story_state', 'action_items',
                    'ceremony_summaries', 'learning_index'
                )
                ORDER BY name
                """
            )

            tables = [row[0] for row in cursor.fetchall()]

            assert len(tables) == 5
            assert "action_items" in tables
            assert "ceremony_summaries" in tables
            assert "epic_state" in tables
            assert "learning_index" in tables
            assert "story_state" in tables

        finally:
            conn.close()

    def test_creates_indexes(self, db_with_schema_version):
        """Test that migration creates all necessary indexes."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            Migration005.up(conn)

            cursor = conn.cursor()

            # Get all indexes
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_%'
                ORDER BY name
                """
            )

            indexes = [row[0] for row in cursor.fetchall()]

            # Should have indexes for all tables
            assert any("epic_state" in idx for idx in indexes)
            assert any("story_state" in idx for idx in indexes)
            assert any("action_items" in idx for idx in indexes)
            assert any("ceremony" in idx for idx in indexes)
            assert any("learning" in idx for idx in indexes)

            # Check specific composite indexes exist
            assert "idx_story_state_epic_status" in indexes
            assert "idx_action_items_status_due" in indexes
            assert "idx_ceremony_type_date" in indexes
            assert "idx_learning_active_category" in indexes

        finally:
            conn.close()

    def test_records_migration_version(self, db_with_schema_version):
        """Test that migration records itself in schema_version table."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            Migration005.up(conn)

            cursor = conn.cursor()
            cursor.execute("SELECT version, description FROM schema_version WHERE version = '005'")

            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "005"
            assert "state tracking" in result[1].lower()

        finally:
            conn.close()

    def test_foreign_key_constraints(self, db_with_schema_version):
        """Test that foreign key constraints are properly set up."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            Migration005.up(conn)

            cursor = conn.cursor()

            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # Insert test epic
            cursor.execute(
                """
                INSERT INTO epic_state (epic_num, title, status, created_at, updated_at)
                VALUES (1, 'Test Epic', 'planning', datetime('now'), datetime('now'))
                """
            )

            # Insert test story referencing epic
            cursor.execute(
                """
                INSERT INTO story_state (
                    epic_num, story_num, title, status, created_at, updated_at
                )
                VALUES (1, 1, 'Test Story', 'pending', datetime('now'), datetime('now'))
                """
            )

            conn.commit()

            # Verify story was inserted
            cursor.execute("SELECT COUNT(*) FROM story_state WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 1

            # Test CASCADE DELETE: deleting epic should delete story
            cursor.execute("DELETE FROM epic_state WHERE epic_num = 1")
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM story_state WHERE epic_num = 1")
            assert cursor.fetchone()[0] == 0

        finally:
            conn.close()

    def test_check_constraints(self, db_with_schema_version):
        """Test that CHECK constraints are enforced."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            Migration005.up(conn)

            cursor = conn.cursor()

            # Test epic_state status check
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO epic_state (epic_num, title, status, created_at, updated_at)
                    VALUES (1, 'Test', 'invalid_status', datetime('now'), datetime('now'))
                    """
                )
                conn.commit()

            conn.rollback()

            # Test story_state status check
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO story_state (
                        epic_num, story_num, title, status, created_at, updated_at
                    )
                    VALUES (1, 1, 'Test', 'invalid_status', datetime('now'), datetime('now'))
                    """
                )
                conn.commit()

            conn.rollback()

            # Test action_items priority check
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO action_items (title, status, priority, created_at, updated_at)
                    VALUES ('Test', 'pending', 'invalid', datetime('now'), datetime('now'))
                    """
                )
                conn.commit()

        finally:
            conn.close()


class TestMigration005Down:
    """Tests for migration down (rollback)."""

    def test_removes_all_tables(self, db_with_schema_version):
        """Test that rollback removes all state tracking tables."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            # Apply migration first
            Migration005.up(conn)

            # Verify tables exist
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name IN (
                    'epic_state', 'story_state', 'action_items',
                    'ceremony_summaries', 'learning_index'
                )
                """
            )
            assert cursor.fetchone()[0] == 5

            # Rollback
            Migration005.down(conn)

            # Verify tables are gone
            cursor.execute(
                """
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='table' AND name IN (
                    'epic_state', 'story_state', 'action_items',
                    'ceremony_summaries', 'learning_index'
                )
                """
            )
            assert cursor.fetchone()[0] == 0

        finally:
            conn.close()

    def test_removes_migration_record(self, db_with_schema_version):
        """Test that rollback removes migration record."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            # Apply migration first
            Migration005.up(conn)

            # Verify record exists
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM schema_version WHERE version = '005'")
            assert cursor.fetchone()[0] == 1

            # Rollback
            Migration005.down(conn)

            # Verify record is gone
            cursor.execute("SELECT COUNT(*) FROM schema_version WHERE version = '005'")
            assert cursor.fetchone()[0] == 0

        finally:
            conn.close()


class TestMigration005IsApplied:
    """Tests for is_applied check."""

    def test_returns_false_when_not_applied(self, db_with_schema_version):
        """Test that is_applied returns False before migration."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            assert Migration005.is_applied(conn) is False
        finally:
            conn.close()

    def test_returns_true_when_applied(self, db_with_schema_version):
        """Test that is_applied returns True after migration."""
        conn = sqlite3.connect(str(db_with_schema_version))

        try:
            Migration005.up(conn)
            assert Migration005.is_applied(conn) is True
        finally:
            conn.close()

    def test_returns_false_when_no_schema_version_table(self, temp_db):
        """Test that is_applied returns False when schema_version table doesn't exist."""
        conn = sqlite3.connect(str(temp_db))

        try:
            assert Migration005.is_applied(conn) is False
        finally:
            conn.close()
